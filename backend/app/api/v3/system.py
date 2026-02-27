"""
api/v3/system.py
================
Read-only system-info endpoints (no side-effects).

Routes
------
GET /api/v3/processors   — available document processors
GET /api/v3/languages    — supported OCR languages
GET /api/v3/stats        — in-memory processing counters
GET /api/v3/health       — detailed component health check

Authentication
--------------
All routes require JWT Bearer token **or** API key (``@token_or_api_key_required``).
The ``/api/v3/health`` route is intentionally unauthenticated to allow
monitoring systems to probe it without credentials.
"""
from __future__ import annotations

import time
import logging
from datetime import datetime, timezone

import pytesseract
from flask import Blueprint, current_app, jsonify, request
from sqlalchemy import text

from app.auth.jwt_utils import token_or_api_key_required
from app.processors.registry import processor_registry
from app.language_detector import get_languages_info
from app.database import db
from app.rate_limiter import ratelimit_light

logger = logging.getLogger(__name__)

v3_system_bp = Blueprint("v3_system", __name__, url_prefix="/api/v3")


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@v3_system_bp.route("/processors", methods=["GET"])
@token_or_api_key_required
@ratelimit_light()
def get_processors():
    """
    List available document processors.
    ---
    tags:
      - System
    operationId: getProcessorsV3
    summary: Get all registered document processor modules
    description: >
      Returns the list of document-type processor modules currently registered
      in the processor registry, together with capability metadata.

      Results are cached for 1 hour using the application cache.

      **Authentication**: JWT Bearer token or API key required.

      **Rate limit**: 60 requests / minute per IP.
    responses:
      200:
        description: Processor list retrieved successfully.
    """
    cache_key = "v3:processors_list"

    # Try application cache first
    app_cache = getattr(current_app, "cache", None)
    if app_cache:
        cached = app_cache.get(cache_key)
        if cached:
            return jsonify(cached), 200

    processors = processor_registry.get_processor_info()
    response_body = {
        "processors": processors,
        "total": len(processors),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

    if app_cache:
        try:
            app_cache.set(cache_key, response_body, timeout=3600)
        except Exception as exc:
            logger.warning("Failed to cache processors list: %s", exc)

    return jsonify(response_body), 200


@v3_system_bp.route("/languages", methods=["GET"])
@token_or_api_key_required
@ratelimit_light()
def get_languages():
    """
    List supported OCR languages.
    ---
    tags:
      - System
    operationId: getLanguagesV3
    summary: Get all Tesseract language packs available on this server
    description: >
      Queries the installed Tesseract language data files and returns a
      list of ISO 639-3 codes together with human-readable names.

      **Authentication**: JWT Bearer token or API key required.

      **Rate limit**: 60 requests / minute per IP.
    responses:
      200:
        description: Language list retrieved successfully.
      500:
        description: Failed to query Tesseract for installed languages.
    """
    try:
        languages = get_languages_info()
        return jsonify({
            "success": True,
            "languages": languages,
            "total": len(languages),
        }), 200
    except Exception as exc:
        logger.error("Failed to retrieve language list: %s", exc)
        return jsonify({
            "success": False,
            "error": str(exc),
            "languages": [{"code": "eng", "name": "English"}],
            "total": 1,
        }), 500


@v3_system_bp.route("/stats", methods=["GET"])
@token_or_api_key_required
@ratelimit_light()
def get_stats():
    """
    Get system-level processing statistics.
    ---
    tags:
      - System
    operationId: getStatsV3
    summary: Aggregate in-memory scan counters and processor registry stats
    description: >
      Returns current in-memory counters for document scans (reset on
      server restart) plus processor-registry metadata.  For persisted
      analytics use ``GET /api/v3/analytics/dashboard``.

      **Authentication**: JWT Bearer token or API key required.

      **Rate limit**: 60 requests / minute per IP.
    responses:
      200:
        description: Statistics retrieved successfully.
    """
    try:
        supported_docs = processor_registry.list_supported_documents()
        processor_count = len(processor_registry.processors)

        # Pull from analytics engine if available
        db_stats: dict = {}
        try:
            from app.database import ScanHistory
            total_db = ScanHistory.query.count()
            db_stats = {"total_db_scans": total_db}
        except Exception:
            pass

        return jsonify({
            "success": True,
            "processors": {
                "total": processor_count,
                "supported_documents": supported_docs,
            },
            "database": db_stats,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }), 200
    except Exception as exc:
        logger.error("Stats endpoint error: %s", exc)
        return jsonify({"success": False, "error": str(exc)}), 500


@v3_system_bp.route("/health", methods=["GET"])
@ratelimit_light()
def health_check():
    """
    Detailed component health check (v3).
    ---
    tags:
      - Health
    operationId: healthCheckV3System
    summary: Probe database, OCR engine, cache, and rate-limiter
    description: >
      Returns ``status: healthy`` (HTTP 200) when all probed components are
      operational, ``status: degraded`` (HTTP 200) when minor issues are
      detected, or ``status: unhealthy`` (HTTP 503) when a critical component
      is down.

      This endpoint is intentionally **unauthenticated** to permit external
      monitoring systems (e.g. Kubernetes liveness probes) to call it without
      credentials.

      **Rate limit**: 60 requests / minute per IP.
    responses:
      200:
        description: Health check completed — inspect the `status` field.
      503:
        description: One or more critical components are unhealthy.
    """
    try:
        health_status: dict = {
            "status": "healthy",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "version": "3.0",
            "services": {},
        }

        # Database
        try:
            db.session.execute(text("SELECT 1"))
            health_status["services"]["database"] = "healthy"
        except Exception as exc:
            logger.error("Database health check failed: %s", exc)
            health_status["services"]["database"] = "unhealthy"
            health_status["status"] = "degraded"

        # OCR engine
        try:
            pytesseract.get_tesseract_version()
            health_status["services"]["ocr_engine"] = "healthy"
        except Exception:
            health_status["services"]["ocr_engine"] = "unhealthy"
            health_status["status"] = "degraded"

        # Cache
        app_cache = getattr(current_app, "cache", None)
        if app_cache:
            try:
                app_cache.set("_health_probe", "ok", timeout=1)
                val = app_cache.get("_health_probe")
                health_status["services"]["cache"] = "healthy" if val == "ok" else "unhealthy"
                app_cache.delete("_health_probe")
            except Exception as exc:
                logger.error("Cache health check failed: %s", exc)
                health_status["services"]["cache"] = "unavailable"
        else:
            health_status["services"]["cache"] = "not_configured"

        # Rate limiter
        health_status["services"]["rate_limiter"] = (
            "healthy" if current_app.config.get("RATE_LIMIT_ENABLED") else "disabled"
        )

        status_code = 200 if health_status["status"] == "healthy" else 503
        return jsonify(health_status), status_code

    except Exception as exc:
        return jsonify({
            "status": "unhealthy",
            "error": str(exc),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }), 503
