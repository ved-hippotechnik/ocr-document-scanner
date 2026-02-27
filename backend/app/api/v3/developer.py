"""
api/v3/developer.py
===================
Developer-portal self-service endpoints.

Routes (url_prefix=/api/v3/developer)
----------------------------------------
GET    /api/v3/developer/keys                          — list API keys
POST   /api/v3/developer/keys                          — create API key
PATCH  /api/v3/developer/keys/<key_id>                 — update API key
DELETE /api/v3/developer/keys/<key_id>                 — revoke API key
GET    /api/v3/developer/usage                         — usage overview
GET    /api/v3/developer/usage/keys/<key_id>           — per-key usage
GET    /api/v3/developer/webhooks                      — list webhooks
POST   /api/v3/developer/webhooks                      — create webhook
PATCH  /api/v3/developer/webhooks/<webhook_id>         — update webhook
DELETE /api/v3/developer/webhooks/<webhook_id>         — delete webhook
POST   /api/v3/developer/webhooks/<webhook_id>/test    — send test event
GET    /api/v3/developer/webhooks/<webhook_id>/deliveries — delivery log

Implementation consolidated from ``app/developer/routes.py``.

Authentication
--------------
All routes require a JWT Bearer token (``@token_required``).  API-key
authentication is intentionally excluded here because API-key management
must be done by an authenticated human user, not by an API key itself.
"""
from __future__ import annotations

import json
import logging
from datetime import datetime, timedelta, timezone

from flask import Blueprint, jsonify, request
from sqlalchemy import func

from app.auth.jwt_utils import token_required
from app.database import db, ApiKey, WebhookConfig, WebhookDelivery, ApiUsageLog
from .responses import api_success, api_error

logger = logging.getLogger(__name__)

v3_developer_bp = Blueprint("v3_developer", __name__, url_prefix="/api/v3/developer")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _empty_summary() -> dict:
    return {
        "total_requests": 0,
        "total_errors": 0,
        "success_rate": 100.0,
        "active_keys": 0,
    }


# ---------------------------------------------------------------------------
# API Key Management
# ---------------------------------------------------------------------------

@v3_developer_bp.route("/keys", methods=["GET"])
@token_required
def list_keys():
    """List the current user's API keys (key values are masked)."""
    keys = (
        ApiKey.query
        .filter_by(user_id=request.current_user.id)
        .order_by(ApiKey.created_at.desc())
        .all()
    )
    return api_success({"keys": [k.to_dict() for k in keys]})


@v3_developer_bp.route("/keys", methods=["POST"])
@token_required
def create_key():
    """Create a new API key.  The raw key value is returned only once."""
    data = request.get_json(silent=True) or {}
    name = data.get("name", "Default Key")
    scopes = data.get("scopes", ["scan"])
    rate_limit = data.get("rate_limit", 60)

    allowed_scopes = {"scan", "batch", "ai", "analytics"}
    if not set(scopes).issubset(allowed_scopes):
        return api_error(f"Invalid scopes. Allowed: {sorted(allowed_scopes)}", "INVALID_SCOPES")

    rate_limit = max(1, min(rate_limit, 1000))

    raw_key, api_key = ApiKey.generate(
        user_id=request.current_user.id,
        name=name,
        scopes=scopes,
        rate_limit=rate_limit,
    )
    db.session.add(api_key)
    db.session.commit()

    result = api_key.to_dict()
    result["raw_key"] = raw_key  # Shown exactly once
    logger.info("API key created for user %s: %s", request.current_user.id, api_key.key_prefix)
    return api_success(result, 201)


@v3_developer_bp.route("/keys/<int:key_id>", methods=["PATCH"])
@token_required
def update_key(key_id: int):
    """Update an API key's name, scopes, rate limit, or active status."""
    api_key = ApiKey.query.filter_by(id=key_id, user_id=request.current_user.id).first()
    if not api_key:
        return api_error(_KEY_NOT_FOUND, "KEY_NOT_FOUND", 404)

    data = request.get_json(silent=True) or {}

    if "name" in data:
        api_key.name = data["name"]
    if "scopes" in data:
        allowed_scopes = {"scan", "batch", "ai", "analytics"}
        if not set(data["scopes"]).issubset(allowed_scopes):
            return api_error(f"Invalid scopes. Allowed: {sorted(allowed_scopes)}", "INVALID_SCOPES")
        api_key.scopes = json.dumps(data["scopes"])
    if "rate_limit" in data:
        api_key.rate_limit = max(1, min(int(data["rate_limit"]), 1000))
    if "is_active" in data:
        api_key.is_active = bool(data["is_active"])

    db.session.commit()
    return api_success(api_key.to_dict())


@v3_developer_bp.route("/keys/<int:key_id>", methods=["DELETE"])
@token_required
def revoke_key(key_id: int):
    """Permanently deactivate an API key."""
    api_key = ApiKey.query.filter_by(id=key_id, user_id=request.current_user.id).first()
    if not api_key:
        return api_error(_KEY_NOT_FOUND, "KEY_NOT_FOUND", 404)

    api_key.is_active = False
    db.session.commit()
    logger.info("API key revoked: %s (user %s)", api_key.key_prefix, request.current_user.id)
    return api_success({"message": "API key revoked"})


# ---------------------------------------------------------------------------
# Usage Analytics
# ---------------------------------------------------------------------------

_KEY_NOT_FOUND = "API key not found"
_WEBHOOK_NOT_FOUND = "Webhook not found"


@v3_developer_bp.route("/usage", methods=["GET"])
@token_required
def usage_overview():
    """Aggregated usage stats for all of the current user's API keys."""
    days = request.args.get("days", 30, type=int)
    days = max(1, min(days, 365))

    user_key_ids = [
        k.id for k in ApiKey.query.filter_by(user_id=request.current_user.id).all()
    ]
    if not user_key_ids:
        return api_success({"usage": [], "summary": _empty_summary()})

    start_date = datetime.now(timezone.utc).date() - timedelta(days=days)

    rows = (
        db.session.query(
            ApiUsageLog.date,
            func.sum(ApiUsageLog.request_count).label("requests"),
            func.sum(ApiUsageLog.error_count).label("errors"),
        )
        .filter(
            ApiUsageLog.api_key_id.in_(user_key_ids),
            ApiUsageLog.date >= start_date,
        )
        .group_by(ApiUsageLog.date)
        .order_by(ApiUsageLog.date)
        .all()
    )

    usage = [
        {"date": r.date.isoformat(), "requests": r.requests, "errors": r.errors}
        for r in rows
    ]
    total_requests = sum(r.requests for r in rows)
    total_errors = sum(r.errors for r in rows)

    return api_success({
        "usage": usage,
        "summary": {
            "total_requests": total_requests,
            "total_errors": total_errors,
            "success_rate": (
                round((1 - total_errors / total_requests) * 100, 2)
                if total_requests > 0
                else 100.0
            ),
            "active_keys": len([
                k for k in ApiKey.query.filter_by(
                    user_id=request.current_user.id, is_active=True
                ).all()
            ]),
        },
    })


@v3_developer_bp.route("/usage/keys/<int:key_id>", methods=["GET"])
@token_required
def usage_by_key(key_id: int):
    """Per-key usage breakdown grouped by endpoint and date."""
    api_key = ApiKey.query.filter_by(id=key_id, user_id=request.current_user.id).first()
    if not api_key:
        return api_error(_KEY_NOT_FOUND, "KEY_NOT_FOUND", 404)

    days = request.args.get("days", 30, type=int)
    days = max(1, min(days, 365))
    start_date = datetime.now(timezone.utc).date() - timedelta(days=days)

    rows = (
        ApiUsageLog.query
        .filter(ApiUsageLog.api_key_id == key_id, ApiUsageLog.date >= start_date)
        .order_by(ApiUsageLog.date.desc())
        .all()
    )
    return api_success({"key": api_key.to_dict(), "usage": [r.to_dict() for r in rows]})


# ---------------------------------------------------------------------------
# Webhook Management
# ---------------------------------------------------------------------------

@v3_developer_bp.route("/webhooks", methods=["GET"])
@token_required
def list_webhooks():
    """List the current user's webhook configurations."""
    webhooks = (
        WebhookConfig.query
        .filter_by(user_id=request.current_user.id)
        .order_by(WebhookConfig.created_at.desc())
        .all()
    )
    return api_success({"webhooks": [w.to_dict() for w in webhooks]})


@v3_developer_bp.route("/webhooks", methods=["POST"])
@token_required
def create_webhook():
    """Create a webhook configuration.  The signing secret is returned once."""
    data = request.get_json(silent=True) or {}
    url = data.get("url")
    if not url:
        return api_error("url is required", "URL_REQUIRED")

    allowed_events = {"scan.complete", "scan.error", "batch.complete", "batch.error"}
    events = data.get("events", ["scan.complete"])
    if not set(events).issubset(allowed_events):
        return api_error(f"Invalid events. Allowed: {sorted(allowed_events)}", "INVALID_EVENTS")

    webhook = WebhookConfig.create(
        user_id=request.current_user.id,
        url=url,
        events=events,
    )
    db.session.add(webhook)
    db.session.commit()

    result = webhook.to_dict(include_secret=True)
    logger.info("Webhook created for user %s: %s", request.current_user.id, webhook.id)
    return api_success(result, 201)


@v3_developer_bp.route("/webhooks/<int:webhook_id>", methods=["PATCH"])
@token_required
def update_webhook(webhook_id: int):
    """Update a webhook's URL, events, or active status."""
    webhook = WebhookConfig.query.filter_by(
        id=webhook_id, user_id=request.current_user.id
    ).first()
    if not webhook:
        return api_error(_WEBHOOK_NOT_FOUND, "WEBHOOK_NOT_FOUND", 404)

    data = request.get_json(silent=True) or {}
    if "url" in data:
        webhook.url = data["url"]
    if "events" in data:
        allowed_events = {"scan.complete", "scan.error", "batch.complete", "batch.error"}
        if not set(data["events"]).issubset(allowed_events):
            return api_error(f"Invalid events. Allowed: {sorted(allowed_events)}", "INVALID_EVENTS")
        webhook.events = json.dumps(data["events"])
    if "is_active" in data:
        webhook.is_active = bool(data["is_active"])

    db.session.commit()
    return api_success(webhook.to_dict())


@v3_developer_bp.route("/webhooks/<int:webhook_id>", methods=["DELETE"])
@token_required
def delete_webhook(webhook_id: int):
    """Delete a webhook configuration and all its delivery history."""
    webhook = WebhookConfig.query.filter_by(
        id=webhook_id, user_id=request.current_user.id
    ).first()
    if not webhook:
        return api_error(_WEBHOOK_NOT_FOUND, "WEBHOOK_NOT_FOUND", 404)

    db.session.delete(webhook)
    db.session.commit()
    logger.info("Webhook deleted: %s (user %s)", webhook_id, request.current_user.id)
    return api_success({"message": "Webhook deleted"})


@v3_developer_bp.route("/webhooks/<int:webhook_id>/test", methods=["POST"])
@token_required
def test_webhook(webhook_id: int):
    """Send a test event delivery to the webhook URL."""
    webhook = WebhookConfig.query.filter_by(
        id=webhook_id, user_id=request.current_user.id
    ).first()
    if not webhook:
        return api_error(_WEBHOOK_NOT_FOUND, "WEBHOOK_NOT_FOUND", 404)

    from app.webhooks import send_webhook_to_config
    delivery = send_webhook_to_config(
        webhook,
        event_type="test",
        payload={"message": "This is a test webhook delivery"},
        async_send=False,
    )
    return api_success({
        "message": "Test webhook sent",
        "delivery": delivery.to_dict() if delivery else None,
    })


@v3_developer_bp.route("/webhooks/<int:webhook_id>/deliveries", methods=["GET"])
@token_required
def list_deliveries(webhook_id: int):
    """View delivery log for a specific webhook (paginated)."""
    webhook = WebhookConfig.query.filter_by(
        id=webhook_id, user_id=request.current_user.id
    ).first()
    if not webhook:
        return api_error(_WEBHOOK_NOT_FOUND, "WEBHOOK_NOT_FOUND", 404)

    page = request.args.get("page", 1, type=int)
    per_page = min(request.args.get("per_page", 20, type=int), 100)

    pagination = (
        WebhookDelivery.query
        .filter_by(webhook_config_id=webhook_id)
        .order_by(WebhookDelivery.created_at.desc())
        .paginate(page=page, per_page=per_page, error_out=False)
    )

    return api_success({
        "deliveries": [d.to_dict() for d in pagination.items],
        "total": pagination.total,
        "page": pagination.page,
        "pages": pagination.pages,
    })
