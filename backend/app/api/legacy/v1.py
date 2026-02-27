"""
api/legacy/v1.py
================
Thin deprecation-proxy for v1 routes (``/api/*``).

Every route in this blueprint forwards the incoming request to the
corresponding v3 handler by calling it directly (function-to-function
delegation — no HTTP round-trip).  A ``Deprecation: true`` header and a
``Sunset`` header are injected into every response, and a WARNING-level log
entry is written so operators can track remaining v1 usage.

Routes proxied
--------------
POST /api/scan           → v3 scan_document_v3
GET  /api/stats          → v3 get_stats
GET  /api/documents      → v1 fallback (served locally; no v3 equivalent)
POST /api/reset-stats    → v1 fallback (served locally; in-memory only)
GET  /api/document-types → v3 system (document type catalogue)
GET  /api/languages      → v3 get_languages

Deprecation notice
------------------
These routes are deprecated and will be removed in a future release.
Please migrate to the v3 equivalents:

  POST /api/scan           →  POST /api/v3/scan
  GET  /api/stats          →  GET  /api/v3/stats
  GET  /api/document-types →  GET  /api/v3/processors
  GET  /api/languages      →  GET  /api/v3/languages

Authentication
--------------
v1 routes are intentionally **unauthenticated** to maintain full backward
compatibility for callers that did not previously supply credentials.
"""
from __future__ import annotations

import logging
from datetime import date, timedelta

from flask import Blueprint, jsonify, make_response, request

logger = logging.getLogger(__name__)

legacy_v1_bp = Blueprint("legacy_v1", __name__)

# Sunset date — give consumers 6 months from today
_SUNSET_DATE = (date.today() + timedelta(days=180)).strftime("%a, %d %b %Y 00:00:00 GMT")


def _deprecation_response(resp):
    """Attach standard deprecation headers to a Flask response."""
    resp.headers["Deprecation"] = "true"
    resp.headers["Sunset"] = _SUNSET_DATE
    resp.headers["Link"] = '</api/v3>; rel="successor-version"'
    return resp


def _warn(endpoint: str) -> None:
    logger.warning(
        "Deprecated v1 endpoint called: %s — migrate to /api/v3", endpoint
    )


# ---------------------------------------------------------------------------
# POST /api/scan  →  POST /api/v3/scan
# ---------------------------------------------------------------------------

@legacy_v1_bp.route("/api/scan", methods=["POST"])
def legacy_scan():
    """Deprecated.  Use POST /api/v3/scan instead."""
    _warn("/api/scan")
    # Delegate to the v3 handler directly (within the same process)
    from app.api.v3.scan import scan_document_v3
    result = scan_document_v3()
    resp = make_response(result)
    return _deprecation_response(resp)


# ---------------------------------------------------------------------------
# GET /api/stats  →  GET /api/v3/stats
# ---------------------------------------------------------------------------

@legacy_v1_bp.route("/api/stats", methods=["GET"])
def legacy_stats():
    """Deprecated.  Use GET /api/v3/stats instead."""
    _warn("/api/stats")
    from app.api.v3.system import get_stats
    result = get_stats()
    resp = make_response(result)
    return _deprecation_response(resp)


# ---------------------------------------------------------------------------
# GET /api/documents  — served locally (in-memory store, no v3 equivalent)
# ---------------------------------------------------------------------------

@legacy_v1_bp.route("/api/documents", methods=["GET"])
def legacy_documents():
    """Deprecated.  Returns in-memory document list (resets on server restart)."""
    _warn("/api/documents")
    # The document list lives in the v1 routes module's in-memory store
    from app.routes import document_stats
    documents = []
    if document_stats.get("documents"):
        for i, record in enumerate(document_stats["documents"]):
            documents.append({
                "id": i + 1,
                "document_type": record.get("document_type", "unknown"),
                "nationality": record.get("nationality", "UNKNOWN"),
                "timestamp": record.get("timestamp", ""),
                "status": "processed",
                "full_name": record.get("full_name"),
                "document_number": record.get("document_number"),
                "date_of_birth": record.get("date_of_birth"),
                "date_of_expiry": record.get("date_of_expiry"),
                "gender": record.get("gender"),
                "place_of_issue": record.get("place_of_issue"),
                "issue_date": record.get("issue_date"),
                "unified_number": record.get("unified_number"),
            })
    else:
        for i, record in enumerate(document_stats.get("scan_history", [])):
            extracted_info = record.get("extracted_info", {})
            documents.append({
                "id": i + 1,
                "document_type": record.get("document_type", "unknown"),
                "nationality": record.get("nationality", "UNKNOWN"),
                "timestamp": record.get("timestamp", ""),
                "status": "processed",
                "extracted_info": extracted_info,
                "full_name": extracted_info.get("full_name"),
                "document_number": extracted_info.get("document_number"),
                "date_of_birth": extracted_info.get("date_of_birth"),
                "date_of_expiry": extracted_info.get("date_of_expiry"),
                "gender": extracted_info.get("gender"),
                "place_of_issue": extracted_info.get("place_of_issue"),
                "issue_date": extracted_info.get("issue_date"),
                "unified_number": extracted_info.get("unified_number"),
                "license_number": extracted_info.get("license_number"),
            })

    resp = make_response(jsonify({
        "success": True,
        "documents": documents,
        "total": len(documents),
    }))
    return _deprecation_response(resp)


# ---------------------------------------------------------------------------
# POST /api/reset-stats  — served locally (in-memory only)
# ---------------------------------------------------------------------------

@legacy_v1_bp.route("/api/reset-stats", methods=["POST"])
def legacy_reset_stats():
    """Deprecated.  Resets in-memory statistics only (no database effect)."""
    _warn("/api/reset-stats")
    import app.routes as _routes_module
    _routes_module.document_stats = {
        "total_scanned": 0,
        "document_types": {
            "passport": 0, "id_card": 0, "driving_license": 0,
            "aadhaar": 0, "us_green_card": 0, "other": 0,
        },
        "nationalities": {},
        "scan_history": [],
        "documents": [],
    }
    resp = make_response(jsonify({"success": True, "message": "Statistics reset successfully"}))
    return _deprecation_response(resp)


# ---------------------------------------------------------------------------
# GET /api/document-types  →  served locally (static catalogue)
# ---------------------------------------------------------------------------

@legacy_v1_bp.route("/api/document-types", methods=["GET"])
def legacy_document_types():
    """Deprecated.  Use GET /api/v3/processors instead."""
    _warn("/api/document-types")
    document_types = [
        {"id": "passport",          "name": "Passport",           "description": "Generic international passport document"},
        {"id": "id_card",           "name": "ID Card",            "description": "Government issued identification card"},
        {"id": "driving_license",   "name": "Driving License",    "description": "Motor vehicle driving license"},
        {"id": "aadhaar",           "name": "Aadhaar Card",       "description": "Indian unique identification card"},
        {"id": "us_green_card",     "name": "US Green Card",      "description": "US Permanent Resident Card"},
        {"id": "uk_passport",       "name": "UK Passport",        "description": "United Kingdom passport"},
        {"id": "canadian_passport", "name": "Canadian Passport",  "description": "Canadian passport"},
        {"id": "australian_passport","name": "Australian Passport","description": "Australian passport"},
        {"id": "german_passport",   "name": "German Passport",    "description": "German passport (Deutscher Reisepass)"},
        {"id": "other",             "name": "Other Document",     "description": "Other government or official documents"},
    ]
    resp = make_response(jsonify({
        "success": True,
        "document_types": document_types,
        "total": len(document_types),
    }))
    return _deprecation_response(resp)


# ---------------------------------------------------------------------------
# GET /api/languages  →  GET /api/v3/languages
# ---------------------------------------------------------------------------

@legacy_v1_bp.route("/api/languages", methods=["GET"])
def legacy_languages():
    """Deprecated.  Use GET /api/v3/languages instead."""
    _warn("/api/languages")
    from app.api.v3.system import get_languages
    result = get_languages()
    resp = make_response(result)
    return _deprecation_response(resp)
