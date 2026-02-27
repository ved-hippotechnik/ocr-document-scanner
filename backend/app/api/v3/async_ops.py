"""
api/v3/async_ops.py
===================
Celery-backed asynchronous document processing endpoints.

Routes (url_prefix=/api/v3/async)
------------------------------------
POST /api/v3/async/scan              — submit a single document for async OCR
POST /api/v3/async/batch             — submit a batch for async processing
GET  /api/v3/async/status/<task_id>  — poll Celery task status
POST /api/v3/async/cancel/<task_id>  — revoke a queued/running task
POST /api/v3/async/analytics/generate — async analytics report generation
POST /api/v3/async/mcp/think         — MCP sequential-thinking document analysis
GET  /api/v3/async/queue/stats        — Celery worker/queue statistics

Implementation ported verbatim from ``app/routes_async.py`` (the
``async_bp`` blueprint) with the url_prefix updated to ``/api/v3/async``.

Authentication
--------------
All routes require a JWT Bearer token (``@token_required``).  API-key
auth is intentionally *not* accepted here because async tasks are tied to
a user identity for ownership verification.
"""
from __future__ import annotations

import logging
from typing import Any, Dict

from flask import Blueprint, current_app, g, jsonify, request

from app.auth.jwt_utils import token_required, get_current_user
from app.database import db, ScanHistory, BatchProcessingJob
from app.resilience import structured_error
from app.tasks import (
    process_document_async,
    batch_process_async,
    generate_analytics_async,
    process_with_mcp_thinking,
)

logger = logging.getLogger(__name__)

v3_async_bp = Blueprint("v3_async", __name__, url_prefix="/api/v3/async")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _check_celery_available():
    """Return a structured 503 response if no Celery workers are responding."""
    celery = getattr(current_app, "celery", None)
    if celery is None:
        return structured_error("Task queue not configured", "CELERY_UNAVAILABLE", 503, component="celery")
    try:
        inspect = celery.control.inspect(timeout=3)
        if not inspect.ping():
            return structured_error("No task workers available", "NO_WORKERS", 503, component="celery")
    except Exception as exc:
        logger.warning("Celery health check failed: %s", exc)
        return structured_error("Task queue unreachable", "CELERY_UNREACHABLE", 503, details=exc, component="celery")
    return None


def _verify_task_ownership(task_id: str):
    """Verify the current authenticated user owns the task.

    Returns a structured error response tuple, or ``None`` if ownership is
    confirmed (or the task record has no user_id — assumed public).
    """
    user = get_current_user()
    scan = ScanHistory.query.filter_by(task_id=task_id).first()
    job = BatchProcessingJob.query.filter_by(task_id=task_id).first()
    owner_id = None
    if scan:
        owner_id = scan.user_id
    elif job:
        owner_id = job.user_id
    if owner_id is not None and owner_id != user.id:
        logger.warning(
            "User %s attempted to access task %s owned by %s",
            user.id, task_id, owner_id,
        )
        return structured_error("Task not found", "TASK_NOT_FOUND", 404)
    return None


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@v3_async_bp.route("/scan", methods=["POST"])
@token_required
def async_scan():
    """Submit a document image for asynchronous OCR processing.

    Returns HTTP 202 immediately with ``task_id`` and ``scan_id`` for
    polling via ``GET /api/v3/async/status/<task_id>``.
    """
    try:
        celery_err = _check_celery_available()
        if celery_err:
            return celery_err

        data = request.get_json()
        if not data or "image" not in data:
            return structured_error("No image data provided", "IMAGE_REQUIRED", 400)

        user = get_current_user()

        scan = ScanHistory(
            user_id=user.id,
            filename=data.get("filename", "async_upload"),
            status="queued",
            document_type=data.get("document_type"),
        )
        db.session.add(scan)
        try:
            db.session.commit()
        except Exception as db_err:
            db.session.rollback()
            return structured_error("Failed to create scan record", "DB_ERROR", 500, details=db_err)

        task = process_document_async.delay(scan.id, data["image"], data.get("document_type"))
        scan.task_id = task.id
        db.session.commit()

        return jsonify({
            "success": True,
            "scan_id": scan.id,
            "task_id": task.id,
            "status": "queued",
            "message": "Document submitted for processing",
            "request_id": getattr(g, "request_id", None),
        }), 202

    except Exception as exc:
        logger.error("Async scan error (request_id=%s): %s", getattr(g, "request_id", "unknown"), exc)
        return structured_error("Async scan failed", "ASYNC_SCAN_ERROR", 500, details=exc)


@v3_async_bp.route("/batch", methods=["POST"])
@token_required
def async_batch():
    """Submit a list of documents for asynchronous batch processing.

    Accepts up to 100 base64-encoded images in ``images`` array.
    Returns HTTP 202 with ``job_id`` and ``task_id``.
    """
    try:
        celery_err = _check_celery_available()
        if celery_err:
            return celery_err

        data = request.get_json()
        if not data or "images" not in data or not isinstance(data["images"], list):
            return structured_error("No images array provided", "IMAGES_REQUIRED", 400)

        if len(data["images"]) > 100:
            return structured_error("Maximum 100 documents per batch", "BATCH_TOO_LARGE", 400)

        user = get_current_user()

        job = BatchProcessingJob(
            user_id=user.id,
            total_documents=len(data["images"]),
            status="queued",
        )
        db.session.add(job)
        try:
            db.session.commit()
        except Exception as db_err:
            db.session.rollback()
            return structured_error("Failed to create batch job", "DB_ERROR", 500, details=db_err)

        task = batch_process_async.delay(job.id, data["images"])
        job.task_id = task.id
        db.session.commit()

        return jsonify({
            "success": True,
            "job_id": job.id,
            "task_id": task.id,
            "status": "queued",
            "total_documents": len(data["images"]),
            "message": "Batch submitted for processing",
            "request_id": getattr(g, "request_id", None),
        }), 202

    except Exception as exc:
        logger.error("Async batch error (request_id=%s): %s", getattr(g, "request_id", "unknown"), exc)
        return structured_error("Async batch failed", "ASYNC_BATCH_ERROR", 500, details=exc)


@v3_async_bp.route("/status/<task_id>", methods=["GET"])
@token_required
def get_task_status(task_id: str):
    """Poll the status of a previously submitted async task."""
    try:
        ownership_err = _verify_task_ownership(task_id)
        if ownership_err:
            return ownership_err

        from celery.result import AsyncResult
        task = AsyncResult(task_id, app=current_app.celery)

        response: Dict[str, Any] = {
            "task_id": task_id,
            "state": task.state,
            "ready": task.ready(),
            "request_id": getattr(g, "request_id", None),
        }

        if task.state == "PENDING":
            response["status"] = "Task not found or pending"
        elif task.state == "PROCESSING":
            response["current"] = task.info
        elif task.state == "SUCCESS":
            response["result"] = task.result
        elif task.state == "FAILURE":
            response["error"] = str(task.info)

        return jsonify(response), 200

    except Exception as exc:
        logger.error("Task status error (request_id=%s): %s", getattr(g, "request_id", "unknown"), exc)
        return structured_error("Failed to get task status", "TASK_STATUS_ERROR", 500, details=exc)


@v3_async_bp.route("/cancel/<task_id>", methods=["POST"])
@token_required
def cancel_task(task_id: str):
    """Revoke (terminate) a queued or running Celery task."""
    try:
        ownership_err = _verify_task_ownership(task_id)
        if ownership_err:
            return ownership_err

        from celery.result import AsyncResult
        task = AsyncResult(task_id, app=current_app.celery)
        task.revoke(terminate=True)

        scan = ScanHistory.query.filter_by(task_id=task_id).first()
        if scan:
            scan.status = "cancelled"
            db.session.commit()

        job = BatchProcessingJob.query.filter_by(task_id=task_id).first()
        if job:
            job.status = "cancelled"
            db.session.commit()

        return jsonify({
            "success": True,
            "task_id": task_id,
            "status": "cancelled",
            "request_id": getattr(g, "request_id", None),
        }), 200

    except Exception as exc:
        logger.error("Task cancel error (request_id=%s): %s", getattr(g, "request_id", "unknown"), exc)
        return structured_error("Failed to cancel task", "TASK_CANCEL_ERROR", 500, details=exc)


@v3_async_bp.route("/analytics/generate", methods=["POST"])
@token_required
def async_generate_analytics():
    """Trigger asynchronous analytics report generation.

    Optional JSON body: ``{ "days": 30, "global": false }``
    """
    try:
        data = request.get_json() or {}
        user = get_current_user()

        task = generate_analytics_async.delay(
            user_id=user.id if not data.get("global", False) else None,
            days=data.get("days", 30),
        )

        return jsonify({
            "success": True,
            "task_id": task.id,
            "status": "generating",
            "message": "Analytics report generation started",
        }), 202

    except Exception as exc:
        logger.error("Analytics generation error (request_id=%s): %s", getattr(g, "request_id", "unknown"), exc)
        return structured_error("Analytics generation failed", "ANALYTICS_ERROR", 500, details=exc)


@v3_async_bp.route("/mcp/think", methods=["POST"])
@token_required
def async_mcp_thinking():
    """Process a document with MCP sequential thinking for enhanced analysis.

    Required JSON body: ``{ "document_id": <id>, "requirements": {} }``
    """
    try:
        data = request.get_json()
        if not data or "document_id" not in data:
            return jsonify({"error": "No document_id provided"}), 400

        task = process_with_mcp_thinking.delay(
            document_id=data["document_id"],
            requirements=data.get("requirements", {}),
        )

        return jsonify({
            "success": True,
            "task_id": task.id,
            "status": "thinking",
            "message": "MCP thinking process started",
        }), 202

    except Exception as exc:
        logger.error("MCP thinking error (request_id=%s): %s", getattr(g, "request_id", "unknown"), exc)
        return structured_error("MCP thinking failed", "MCP_ERROR", 500, details=exc)


@v3_async_bp.route("/queue/stats", methods=["GET"])
@token_required
def get_queue_stats():
    """Return Celery worker statistics and per-queue lengths."""
    try:
        from celery import current_app as celery_app
        inspect = celery_app.control.inspect(timeout=5)

        stats: Dict[str, Any] = {
            "active": inspect.active(),
            "scheduled": inspect.scheduled(),
            "reserved": inspect.reserved(),
            "registered": inspect.registered(),
            "stats": inspect.stats(),
        }

        from kombu import Connection
        with Connection(current_app.config.get("CELERY_BROKER_URL")) as conn:
            queues = ["default", "ocr_processing", "batch_processing", "analytics", "maintenance"]
            queue_lengths: Dict[str, int] = {}
            for queue_name in queues:
                try:
                    queue = conn.SimpleQueue(queue_name)
                    queue_lengths[queue_name] = queue.qsize()
                    queue.close()
                except Exception:
                    queue_lengths[queue_name] = 0

        stats["queue_lengths"] = queue_lengths

        return jsonify({
            "success": True,
            "stats": stats,
            "request_id": getattr(g, "request_id", None),
        }), 200

    except Exception as exc:
        logger.error("Queue stats error (request_id=%s): %s", getattr(g, "request_id", "unknown"), exc)
        return structured_error("Failed to get queue stats", "QUEUE_STATS_ERROR", 500, details=exc)
