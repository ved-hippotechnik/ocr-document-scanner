"""
api/v3/analytics.py
===================
Analytics dashboard and reporting endpoints.

Routes (url_prefix=/api/v3/analytics)
----------------------------------------
GET /api/v3/analytics/dashboard      — full dashboard dataset
GET /api/v3/analytics/overview       — quick overview stats
GET /api/v3/analytics/trends         — daily/hourly processing trends
GET /api/v3/analytics/export         — export report (json/csv/pdf)
GET /api/v3/analytics/real-time      — last-hour stats + live connections
GET /api/v3/analytics/system-health  — system-load metrics (admin only)

Implementation consolidated from ``app/analytics/dashboard.py``.

Authentication
--------------
All routes require JWT Bearer token **or** API key.
``/system-health`` additionally requires the admin role.
"""
from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone

from flask import Blueprint, request

from app.auth.jwt_utils import token_or_api_key_required, admin_required
from app.analytics.dashboard import analytics_engine
from app.database import ScanHistory
from app.cache import cache
from app.validation import ErrorHandler, handle_processing_errors

# Stub for websocket stats (websocket module may not be available)
try:
    from app.websocket import get_connection_stats
except Exception:
    def get_connection_stats():
        return {"total_connections": 0, "active_rooms": 0}

logger = logging.getLogger(__name__)

v3_analytics_bp = Blueprint("v3_analytics", __name__, url_prefix="/api/v3/analytics")


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@v3_analytics_bp.route("/dashboard", methods=["GET"])
@token_or_api_key_required
@handle_processing_errors()
def get_dashboard():
    """
    Full analytics dashboard dataset.
    ---
    tags:
      - Analytics
    operationId: getDashboardV3
    summary: Retrieve comprehensive analytics for the requested time window
    description: >
      Returns an aggregated dashboard payload including overview stats,
      processing trends, document-type breakdowns, quality metrics,
      performance percentiles, error analysis, user activity, and system
      health.  Results are cached for 5 minutes.

      **Authentication**: JWT Bearer token or API key required.
    parameters:
      - in: query
        name: days
        type: integer
        required: false
        default: 30
        description: Time window in days (1–365).
    responses:
      200:
        description: Dashboard data retrieved successfully.
      401:
        description: Authentication required.
      500:
        description: Analytics engine error.
    """
    days = request.args.get("days", 30, type=int)
    if days < 1 or days > 365:
        days = 30

    dashboard_data = analytics_engine.get_dashboard_data(days)
    return ErrorHandler.create_success_response({"dashboard": dashboard_data})


@v3_analytics_bp.route("/overview", methods=["GET"])
@token_or_api_key_required
@handle_processing_errors()
def get_overview():
    """
    Quick overview statistics.
    ---
    tags:
      - Analytics
    operationId: getOverviewV3
    summary: Summary totals for the requested time window
    description: >
      Returns total scans, successful scans, success rate, average
      processing time, and period-over-period growth rate.

      **Authentication**: JWT Bearer token or API key required.
    parameters:
      - in: query
        name: days
        type: integer
        required: false
        default: 7
        description: Time window in days.
    responses:
      200:
        description: Overview data retrieved.
      401:
        description: Authentication required.
    """
    days = request.args.get("days", 7, type=int)
    end_date = datetime.now(timezone.utc)
    start_date = end_date - timedelta(days=days)
    overview = analytics_engine._get_overview_stats(start_date, end_date)
    return ErrorHandler.create_success_response({"overview": overview})


@v3_analytics_bp.route("/trends", methods=["GET"])
@token_or_api_key_required
@handle_processing_errors()
def get_trends():
    """
    Daily and hourly processing trends.
    ---
    tags:
      - Analytics
    operationId: getTrendsV3
    summary: Time-series scan volume and average processing time
    description: >
      Returns daily scan counts, average processing times per day, and
      hourly distribution of scans across the requested time window.

      **Authentication**: JWT Bearer token or API key required.
    parameters:
      - in: query
        name: days
        type: integer
        required: false
        default: 30
        description: Time window in days.
    responses:
      200:
        description: Trend data retrieved.
      401:
        description: Authentication required.
    """
    days = request.args.get("days", 30, type=int)
    end_date = datetime.now(timezone.utc)
    start_date = end_date - timedelta(days=days)
    trends = analytics_engine._get_processing_trends(start_date, end_date)
    return ErrorHandler.create_success_response({"trends": trends})


@v3_analytics_bp.route("/export", methods=["GET"])
@token_or_api_key_required
@handle_processing_errors()
def export_report():
    """
    Export an analytics report.
    ---
    tags:
      - Analytics
    operationId: exportReportV3
    summary: Download an analytics report as JSON, CSV, or PDF
    description: >
      Generates and returns an analytics report in the requested format.
      CSV and PDF exports are placeholders and will include a message
      indicating they are not yet fully implemented.

      **Authentication**: JWT Bearer token or API key required.
    parameters:
      - in: query
        name: days
        type: integer
        required: false
        default: 30
        description: Time window in days.
      - in: query
        name: format
        type: string
        required: false
        default: json
        enum:
          - json
          - csv
          - pdf
        description: Report output format.
    responses:
      200:
        description: Report generated.
      400:
        description: Invalid format parameter.
      401:
        description: Authentication required.
    """
    days = request.args.get("days", 30, type=int)
    report_format = request.args.get("format", "json")

    if report_format not in ("json", "csv", "pdf"):
        return ErrorHandler.create_success_response(
            {"error": "Invalid format. Supported formats: json, csv, pdf"}
        ), 400

    report = analytics_engine.export_analytics_report(days, report_format)

    if report_format == "json":
        return ErrorHandler.create_success_response({"report": report})

    return ErrorHandler.create_success_response({
        "message": f"{report_format.upper()} export completed",
        "data": report,
    })


@v3_analytics_bp.route("/real-time", methods=["GET"])
@token_or_api_key_required
@handle_processing_errors()
def get_real_time_stats():
    """
    Real-time statistics (last hour).
    ---
    tags:
      - Analytics
    operationId: getRealTimeStatsV3
    summary: Last-hour scan count, active WebSocket connections, and cache hit rate
    description: >
      Lightweight polling endpoint suitable for dashboard refresh intervals
      of 30–60 seconds.

      **Authentication**: JWT Bearer token or API key required.
    responses:
      200:
        description: Real-time stats retrieved.
      401:
        description: Authentication required.
    """
    end_date = datetime.now(timezone.utc)
    start_date = end_date - timedelta(hours=1)

    recent_scans = ScanHistory.query.filter(
        ScanHistory.created_at >= start_date
    ).count()

    websocket_stats = get_connection_stats()
    cache_stats = cache.get_stats()

    return ErrorHandler.create_success_response({
        "real_time": {
            "recent_scans": recent_scans,
            "active_connections": websocket_stats.get("total_connections", 0),
            "cache_hit_rate": (
                cache_stats.get("hit_rate", 0) if cache_stats.get("available") else 0
            ),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
    })


@v3_analytics_bp.route("/system-health", methods=["GET"])
@token_or_api_key_required
@admin_required
@handle_processing_errors()
def get_system_health():
    """
    System health metrics (admin only).
    ---
    tags:
      - Analytics
    operationId: getSystemHealthV3
    summary: CPU, memory, disk usage, and database/cache stats
    description: >
      Requires admin role.  Returns low-level system metrics including
      CPU and memory utilisation (via psutil if available), disk usage,
      database record count, and cache statistics.

      **Authentication**: JWT Bearer token or API key required (admin only).
    responses:
      200:
        description: System health data retrieved.
      401:
        description: Authentication required.
      403:
        description: Admin role required.
    """
    health_data = analytics_engine._get_system_health()
    return ErrorHandler.create_success_response({"system_health": health_data})
