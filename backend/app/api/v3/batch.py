"""
api/v3/batch.py
===============
Synchronous (in-process) batch document processing endpoints.

Routes (url_prefix=/api/v3/batch)
-----------------------------------
POST   /api/v3/batch/submit            — queue a batch job
GET    /api/v3/batch/status/<job_id>   — poll job status
GET    /api/v3/batch/results/<job_id>  — fetch completed results
POST   /api/v3/batch/cancel/<job_id>   — cancel a pending/running job
GET    /api/v3/batch/jobs              — list caller's jobs (paginated)
GET    /api/v3/batch/stats             — caller's aggregate stats
POST   /api/v3/batch/cleanup           — admin: purge old completed jobs
GET    /api/v3/batch/health            — unauthenticated health probe
GET    /api/v3/batch/export/<job_id>   — download results as JSON/CSV/Excel

Implementation consolidated from ``app/batch/routes.py``.

Authentication
--------------
All routes except ``/health`` require JWT Bearer token **or** API key.
``/cleanup`` additionally requires the caller to be an admin.
"""
from __future__ import annotations

import csv
import json
import logging
from datetime import datetime
from io import BytesIO, StringIO
from typing import Dict, List

from flask import Blueprint, Response, jsonify, request

from app.auth.jwt_utils import token_or_api_key_required, get_current_user
from app.batch.processor import batch_manager, BatchStatus
from app.database import db, BatchProcessingJob
from app.rate_limiter import ratelimit_batch, ratelimit_light, ratelimit_medium
from app.validation import validate_json_input
from .responses import api_success, api_error

logger = logging.getLogger(__name__)

v3_batch_bp = Blueprint("v3_batch", __name__, url_prefix="/api/v3/batch")

_USER_NOT_FOUND = "User not found"

# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@v3_batch_bp.route("/submit", methods=["POST"])
@token_or_api_key_required
@ratelimit_batch()
def submit_batch():
    """
    Submit a batch document processing job.
    ---
    tags:
      - Batch
    operationId: submitBatchV3
    summary: Queue multiple documents for asynchronous OCR
    description: >
      Submit up to 100 documents encoded as base64 strings.  Returns a
      ``job_id`` immediately; poll ``GET /api/v3/batch/status/{job_id}`` for
      completion.

      **Authentication**: JWT Bearer token or API key required.

      **Rate limit**: 5 requests / minute per authenticated user.
    responses:
      200:
        description: Batch job queued — job_id returned.
      400:
        description: Validation error.
      401:
        description: Authentication required.
      429:
        description: Rate limit exceeded.
      500:
        description: Internal server error.
    """
    try:
        if not request.is_json:
            return api_error("JSON data required", "JSON_REQUIRED")

        data = request.get_json()

        validation_result = validate_json_input(data)
        if not validation_result["valid"]:
            return api_error(validation_result["message"], "VALIDATION_ERROR")

        if "documents" not in data:
            return api_error("Documents array required", "DOCUMENTS_REQUIRED")

        documents = data["documents"]

        if not isinstance(documents, list) or len(documents) == 0:
            return api_error("Documents array must contain at least one document", "DOCUMENTS_EMPTY")

        if len(documents) > 100:
            return api_error("Maximum 100 documents per batch", "BATCH_TOO_LARGE")

        for i, doc in enumerate(documents):
            if not isinstance(doc, dict):
                return api_error(f"Document {i} must be an object", "INVALID_DOCUMENT")
            if "id" not in doc or "image" not in doc:
                return api_error(f"Document {i} must have id and image fields", "MISSING_FIELDS")
            if not isinstance(doc["id"], str) or not doc["id"].strip():
                return api_error(f"Document {i} id must be a non-empty string", "INVALID_ID")
            if not isinstance(doc["image"], str) or not doc["image"].strip():
                return api_error(f"Document {i} image must be a non-empty string", "INVALID_IMAGE")

        current_user = get_current_user()
        if not current_user:
            return api_error(_USER_NOT_FOUND, "AUTH_REQUIRED", 401)

        config = data.get("config", {})
        job_id = batch_manager.create_job(
            user_id=current_user.id,
            documents=documents,
            job_config=config,
        )

        success = batch_manager.submit_job(job_id)
        if not success:
            return api_error("Failed to submit job for processing", "SUBMIT_FAILED", 500)

        return api_success({
            "job_id": job_id,
            "message": f"Batch job submitted successfully with {len(documents)} documents",
        })

    except Exception as exc:
        logger.error("Error submitting batch job: %s", exc)
        return api_error(str(exc), "INTERNAL_ERROR", 500)


@v3_batch_bp.route("/status/<job_id>", methods=["GET"])
@token_or_api_key_required
def get_job_status(job_id: str):
    """Get status of a batch processing job."""
    try:
        if not job_id or not job_id.strip():
            return api_error("Job ID required", "JOB_ID_REQUIRED")

        current_user = get_current_user()
        if not current_user:
            return api_error(_USER_NOT_FOUND, "AUTH_REQUIRED", 401)

        status = batch_manager.get_job_status(job_id)
        if not status:
            return api_error("Job not found", "JOB_NOT_FOUND", 404)

        if hasattr(status, "user_id") and status.user_id != current_user.id:
            return api_error("Access denied", "FORBIDDEN", 403)

        return api_success({"job_status": status})

    except Exception as exc:
        logger.error("Error getting job status for %s: %s", job_id, exc)
        return api_error(str(exc), "INTERNAL_ERROR", 500)


@v3_batch_bp.route("/results/<job_id>", methods=["GET"])
@token_or_api_key_required
def get_job_results(job_id: str):
    """Get results of a completed batch processing job."""
    try:
        if not job_id or not job_id.strip():
            return api_error("Job ID required", "JOB_ID_REQUIRED")

        current_user = get_current_user()
        if not current_user:
            return api_error(_USER_NOT_FOUND, "AUTH_REQUIRED", 401)

        results = batch_manager.get_job_results(job_id)
        if not results:
            return api_error("Job not found or not completed", "JOB_NOT_FOUND", 404)

        return api_success({"job_results": results})

    except Exception as exc:
        logger.error("Error getting job results for %s: %s", job_id, exc)
        return api_error(str(exc), "INTERNAL_ERROR", 500)


@v3_batch_bp.route("/cancel/<job_id>", methods=["POST"])
@token_or_api_key_required
def cancel_job(job_id: str):
    """Cancel a batch processing job."""
    try:
        if not job_id or not job_id.strip():
            return api_error("Job ID required", "JOB_ID_REQUIRED")

        current_user = get_current_user()
        if not current_user:
            return api_error(_USER_NOT_FOUND, "AUTH_REQUIRED", 401)

        job_record = BatchProcessingJob.query.filter_by(job_id=job_id).first()
        if not job_record:
            return api_error("Job not found", "JOB_NOT_FOUND", 404)

        if job_record.user_id != current_user.id:
            return api_error("Access denied", "FORBIDDEN", 403)

        success = batch_manager.cancel_job(job_id)
        if not success:
            return api_error("Failed to cancel job — may already be completed", "CANCEL_FAILED")

        return api_success({"message": "Job cancelled successfully"})

    except Exception as exc:
        logger.error("Error cancelling job %s: %s", job_id, exc)
        return api_error(str(exc), "INTERNAL_ERROR", 500)


@v3_batch_bp.route("/jobs", methods=["GET"])
@token_or_api_key_required
def list_user_jobs():
    """List all batch jobs for the current user (paginated)."""
    try:
        current_user = get_current_user()
        if not current_user:
            return api_error(_USER_NOT_FOUND, "AUTH_REQUIRED", 401)

        page = request.args.get("page", 1, type=int)
        per_page = min(request.args.get("per_page", 10, type=int), 100)
        status_filter = request.args.get("status")

        query = BatchProcessingJob.query.filter_by(user_id=current_user.id)
        if status_filter:
            query = query.filter_by(status=status_filter)
        query = query.order_by(BatchProcessingJob.created_at.desc())

        jobs = query.paginate(page=page, per_page=per_page, error_out=False)

        return api_success({
            "jobs": [job.to_dict() for job in jobs.items],
            "pagination": {
                "page": page,
                "per_page": per_page,
                "total": jobs.total,
                "pages": jobs.pages,
                "has_next": jobs.has_next,
                "has_prev": jobs.has_prev,
            },
        })

    except Exception as exc:
        logger.error("Error listing jobs: %s", exc)
        return api_error(str(exc), "INTERNAL_ERROR", 500)


@v3_batch_bp.route("/stats", methods=["GET"])
@token_or_api_key_required
def get_batch_stats():
    """Get batch processing statistics for the current user."""
    try:
        current_user = get_current_user()
        if not current_user:
            return api_error(_USER_NOT_FOUND, "AUTH_REQUIRED", 401)

        user_stats = db.session.query(
            db.func.count(BatchProcessingJob.id).label("total_jobs"),
            db.func.count(
                db.case([(BatchProcessingJob.status == "completed", 1)])
            ).label("completed_jobs"),
            db.func.count(
                db.case([(BatchProcessingJob.status == "failed", 1)])
            ).label("failed_jobs"),
            db.func.count(
                db.case([(BatchProcessingJob.status == "processing", 1)])
            ).label("processing_jobs"),
            db.func.sum(BatchProcessingJob.total_documents).label("total_documents"),
            db.func.sum(BatchProcessingJob.successful_extractions).label("successful_extractions"),
        ).filter_by(user_id=current_user.id).first()

        manager_stats = batch_manager.get_manager_stats()

        return api_success({
            "user_stats": {
                "total_jobs": user_stats.total_jobs or 0,
                "completed_jobs": user_stats.completed_jobs or 0,
                "failed_jobs": user_stats.failed_jobs or 0,
                "processing_jobs": user_stats.processing_jobs or 0,
                "total_documents": user_stats.total_documents or 0,
                "successful_extractions": user_stats.successful_extractions or 0,
                "success_rate": (
                    user_stats.successful_extractions / user_stats.total_documents
                    if user_stats.total_documents
                    else 0
                ),
            },
            "system_stats": manager_stats,
        })

    except Exception as exc:
        logger.error("Error getting batch stats: %s", exc)
        return api_error(str(exc), "INTERNAL_ERROR", 500)


@v3_batch_bp.route("/cleanup", methods=["POST"])
@token_or_api_key_required
def cleanup_jobs():
    """Admin: clean up old completed jobs.

    Requires the authenticated user to have admin role.
    """
    try:
        current_user = get_current_user()
        if not current_user:
            return api_error(_USER_NOT_FOUND, "AUTH_REQUIRED", 401)

        if not current_user.is_admin():
            return api_error("Admin access required", "ADMIN_REQUIRED", 403)

        max_age_hours = (
            request.json.get("max_age_hours", 24) if request.is_json else 24
        )
        batch_manager.cleanup_completed_jobs(max_age_hours)

        return api_success({
            "message": f"Cleaned up jobs older than {max_age_hours} hours",
        })

    except Exception as exc:
        logger.error("Error cleaning up jobs: %s", exc)
        return api_error(str(exc), "INTERNAL_ERROR", 500)


@v3_batch_bp.route("/health", methods=["GET"])
def batch_health():
    """Unauthenticated health probe for the batch processing service."""
    try:
        stats = batch_manager.get_manager_stats()
        is_healthy = (
            stats["active_jobs"] < stats["max_workers"] * 2
            and stats["success_rate"] > 0.8
        )
        return api_success({
            "service": "Batch Processing",
            "status": "healthy" if is_healthy else "degraded",
            "stats": stats,
        })
    except Exception as exc:
        logger.error("Batch service health check failed: %s", exc)
        return api_error(str(exc), "HEALTH_CHECK_FAILED", 500)


@v3_batch_bp.route("/export/<job_id>", methods=["GET"])
@token_or_api_key_required
def export_job_results(job_id: str):
    """Export batch job results as JSON, CSV, or Excel."""
    try:
        if not job_id or not job_id.strip():
            return api_error("Job ID required", "JOB_ID_REQUIRED")

        current_user = get_current_user()
        if not current_user:
            return api_error(_USER_NOT_FOUND, "AUTH_REQUIRED", 401)

        export_format = request.args.get("format", "json").lower()
        if export_format not in ("json", "csv", "excel"):
            return api_error("Unsupported format. Use json, csv, or excel", "INVALID_FORMAT")

        results = batch_manager.get_job_results(job_id)
        if not results:
            return api_error("Job not found or not completed", "JOB_NOT_FOUND", 404)

        if export_format == "json":
            return Response(
                json.dumps(results, indent=2),
                mimetype="application/json",
                headers={"Content-Disposition": f"attachment; filename=batch_results_{job_id}.json"},
            )

        if export_format == "csv":
            output = StringIO()
            writer = csv.writer(output)
            writer.writerow([
                "Document ID", "Success", "Document Type",
                "Confidence", "Quality Score", "Error",
            ])
            for result in results.get("results", []):
                writer.writerow([
                    result.get("document_id", ""),
                    result.get("success", False),
                    result.get("classification", {}).get("document_type", ""),
                    result.get("classification", {}).get("confidence", 0),
                    result.get("quality_score", 0),
                    result.get("error", ""),
                ])
            return Response(
                output.getvalue(),
                mimetype="text/csv",
                headers={"Content-Disposition": f"attachment; filename=batch_results_{job_id}.csv"},
            )

        # excel
        try:
            import pandas as pd
        except ImportError:
            return api_error("pandas is required for Excel export", "MISSING_DEPENDENCY", 500)

        data_rows = [
            {
                "Document ID": r.get("document_id", ""),
                "Success": r.get("success", False),
                "Document Type": r.get("classification", {}).get("document_type", ""),
                "Confidence": r.get("classification", {}).get("confidence", 0),
                "Quality Score": r.get("quality_score", 0),
                "Error": r.get("error", ""),
            }
            for r in results.get("results", [])
        ]
        df = pd.DataFrame(data_rows)
        output_buf = BytesIO()
        with pd.ExcelWriter(output_buf, engine="xlsxwriter") as writer:
            df.to_excel(writer, index=False, sheet_name="Batch Results")
        output_buf.seek(0)

        return Response(
            output_buf.read(),
            mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename=batch_results_{job_id}.xlsx"},
        )

    except Exception as exc:
        logger.error("Error exporting job results for %s: %s", job_id, exc)
        return api_error(str(exc), "INTERNAL_ERROR", 500)
