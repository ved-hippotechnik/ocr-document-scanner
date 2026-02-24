"""
Webhook notification system for scan events.

Sends HTTP POST callbacks with HMAC-SHA256 signatures when documents
finish processing, batch jobs complete, or errors occur.  Delivery is
tracked in the database and retried via Celery on failure.
"""
import json
import logging
from datetime import datetime, timezone
from typing import Optional, Dict, Any

import requests as http_requests

from .database import db, WebhookConfig, WebhookDelivery

logger = logging.getLogger(__name__)

# Recognised event types
EVENT_SCAN_COMPLETE = 'scan.complete'
EVENT_SCAN_ERROR = 'scan.error'
EVENT_BATCH_COMPLETE = 'batch.complete'
EVENT_BATCH_ERROR = 'batch.error'

# Retry back-off schedule (seconds)
RETRY_DELAYS = [10, 60, 300]


def dispatch_event(user_id: int, event_type: str, payload: Dict[str, Any]):
    """Fan-out an event to all matching active webhooks for *user_id*.

    Delivery is always asynchronous via Celery when available.
    """
    webhooks = WebhookConfig.query.filter_by(
        user_id=user_id, is_active=True
    ).all()

    for wh in webhooks:
        events = wh.get_events()
        if event_type not in events and event_type != 'test':
            continue
        _enqueue_delivery(wh, event_type, payload)


def send_webhook_to_config(webhook: WebhookConfig, event_type: str,
                           payload: Dict[str, Any],
                           async_send: bool = True) -> Optional[WebhookDelivery]:
    """Send a single webhook delivery to a specific config.

    Used by the developer portal's "test" endpoint and internally.
    """
    body = _build_body(event_type, payload, webhook.id)
    delivery = WebhookDelivery(
        webhook_config_id=webhook.id,
        event_type=event_type,
        payload=json.dumps(body),
    )
    db.session.add(delivery)
    db.session.commit()

    if async_send:
        _enqueue_delivery(webhook, event_type, payload, delivery_id=delivery.id)
        return delivery

    _deliver(delivery.id)
    db.session.refresh(delivery)
    return delivery


# ── Internal helpers ────────────────────────────────────────────────────────

def _build_body(event_type: str, payload: Dict, webhook_id: int) -> Dict:
    return {
        'event': event_type,
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'data': payload,
        'webhook_id': webhook_id,
    }


def _enqueue_delivery(webhook: WebhookConfig, event_type: str,
                      payload: Dict, delivery_id: Optional[int] = None):
    """Create a WebhookDelivery row (if needed) and schedule via Celery."""
    body = _build_body(event_type, payload, webhook.id)

    if delivery_id is None:
        delivery = WebhookDelivery(
            webhook_config_id=webhook.id,
            event_type=event_type,
            payload=json.dumps(body),
        )
        db.session.add(delivery)
        db.session.commit()
        delivery_id = delivery.id

    try:
        from .tasks import deliver_webhook
        deliver_webhook.delay(delivery_id)
    except Exception:
        # Celery unavailable — attempt synchronous delivery
        logger.warning("Celery unavailable, delivering webhook synchronously")
        _deliver(delivery_id)


def _deliver(delivery_id: int) -> bool:
    """Perform the actual HTTP POST for a delivery record."""
    delivery = WebhookDelivery.query.get(delivery_id)
    if delivery is None:
        return False

    webhook = WebhookConfig.query.get(delivery.webhook_config_id)
    if webhook is None or not webhook.is_active:
        return False

    payload_bytes = delivery.payload.encode('utf-8')
    signature = webhook.sign_payload(payload_bytes)

    delivery.attempts = (delivery.attempts or 0) + 1

    try:
        resp = http_requests.post(
            webhook.url,
            data=payload_bytes,
            timeout=10,
            headers={
                'Content-Type': 'application/json',
                'User-Agent': 'OCR-DocumentScanner-Webhook/2.0',
                'X-Webhook-Signature': f'sha256={signature}',
                'X-Webhook-Event': delivery.event_type,
                'X-Webhook-Delivery': str(delivery.id),
            },
        )
        delivery.response_status = resp.status_code
        delivery.response_body = resp.text[:2000] if resp.text else None

        if resp.ok:
            delivery.delivered_at = datetime.now(timezone.utc)
            delivery.next_retry_at = None
            db.session.commit()
            logger.info("Webhook %s delivered (status %s)", delivery.id, resp.status_code)
            return True

    except http_requests.RequestException as exc:
        delivery.response_status = 0
        delivery.response_body = str(exc)[:2000]

    # Schedule retry if attempts remain
    if delivery.attempts < delivery.max_attempts:
        from datetime import timedelta
        delay_idx = min(delivery.attempts - 1, len(RETRY_DELAYS) - 1)
        delivery.next_retry_at = datetime.now(timezone.utc) + timedelta(seconds=RETRY_DELAYS[delay_idx])
    else:
        delivery.next_retry_at = None

    db.session.commit()
    logger.warning("Webhook %s delivery attempt %s/%s failed",
                    delivery.id, delivery.attempts, delivery.max_attempts)
    return False
