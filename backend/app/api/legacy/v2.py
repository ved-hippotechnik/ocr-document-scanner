"""
api/legacy/v2.py
================
Thin deprecation-proxy for v2 routes (``/api/v2/*``).

Every route forwards the request to the corresponding v3 handler via
direct function delegation (same process, no HTTP round-trip).  A
``Deprecation: true`` header and a ``Sunset`` header are injected into
every response and a WARNING-level log entry is written.

Routes proxied
--------------
POST /api/v2/scan     →  POST /api/v3/scan   (via v3_scan_bp.scan_document_v3)
GET  /api/v2/health   →  GET  /api/v3/health (via v3_system_bp.health_check)
GET  /api/v2/stats    →  GET  /api/v3/stats  (via v3_system_bp.get_stats)
POST /api/v2/classify →  POST /api/v3/classify (via v3_classify_bp.classify_document)
POST /api/v2/quality  →  POST /api/v3/quality  (via v3_classify_bp.quality_check)

Deprecation notice
------------------
These routes are deprecated and will be removed in a future release.
Please migrate to the v3 equivalents listed above.

Authentication
--------------
v2 scan, classify, and quality routes originally required a JWT/API key.
This proxy preserves that requirement by delegating to the v3 handlers
which carry their own ``@token_or_api_key_required`` decorators.  Health
and stats remain open (as they were in v2).

NOTE: Because the v3 handlers include auth decorators via function-level
      decorator application, calling them directly from the proxy also
      enforces those auth checks.
"""
from __future__ import annotations

import logging
from datetime import date, timedelta

from flask import Blueprint, make_response

logger = logging.getLogger(__name__)

legacy_v2_bp = Blueprint("legacy_v2", __name__)

_SUNSET_DATE = (date.today() + timedelta(days=180)).strftime("%a, %d %b %Y 00:00:00 GMT")


def _deprecation_response(resp):
    """Attach standard deprecation headers to a Flask response."""
    resp.headers["Deprecation"] = "true"
    resp.headers["Sunset"] = _SUNSET_DATE
    resp.headers["Link"] = '</api/v3>; rel="successor-version"'
    return resp


def _warn(endpoint: str) -> None:
    logger.warning(
        "Deprecated v2 endpoint called: %s — migrate to /api/v3", endpoint
    )


# ---------------------------------------------------------------------------
# POST /api/v2/scan  →  POST /api/v3/scan
# ---------------------------------------------------------------------------

@legacy_v2_bp.route("/api/v2/scan", methods=["POST"])
def legacy_v2_scan():
    """Deprecated.  Use POST /api/v3/scan instead."""
    _warn("/api/v2/scan")
    from app.api.v3.scan import scan_document_v3
    result = scan_document_v3()
    resp = make_response(result)
    return _deprecation_response(resp)


# ---------------------------------------------------------------------------
# GET /api/v2/health  →  GET /api/v3/health
# ---------------------------------------------------------------------------

@legacy_v2_bp.route("/api/v2/health", methods=["GET"])
def legacy_v2_health():
    """Deprecated.  Use GET /api/v3/health instead."""
    _warn("/api/v2/health")
    from app.api.v3.system import health_check
    result = health_check()
    resp = make_response(result)
    return _deprecation_response(resp)


# ---------------------------------------------------------------------------
# GET /api/v2/stats  →  GET /api/v3/stats
# ---------------------------------------------------------------------------

@legacy_v2_bp.route("/api/v2/stats", methods=["GET"])
def legacy_v2_stats():
    """Deprecated.  Use GET /api/v3/stats instead."""
    _warn("/api/v2/stats")
    from app.api.v3.system import get_stats
    result = get_stats()
    resp = make_response(result)
    return _deprecation_response(resp)


# ---------------------------------------------------------------------------
# POST /api/v2/classify  →  POST /api/v3/classify
# ---------------------------------------------------------------------------

@legacy_v2_bp.route("/api/v2/classify", methods=["POST"])
def legacy_v2_classify():
    """Deprecated.  Use POST /api/v3/classify instead."""
    _warn("/api/v2/classify")
    from app.api.v3.classify import classify_document
    result = classify_document()
    resp = make_response(result)
    return _deprecation_response(resp)


# ---------------------------------------------------------------------------
# POST /api/v2/quality  →  POST /api/v3/quality
# ---------------------------------------------------------------------------

@legacy_v2_bp.route("/api/v2/quality", methods=["POST"])
def legacy_v2_quality():
    """Deprecated.  Use POST /api/v3/quality instead."""
    _warn("/api/v2/quality")
    from app.api.v3.classify import quality_check
    result = quality_check()
    resp = make_response(result)
    return _deprecation_response(resp)
