"""
Webhook notification system for scan events.

Sends HTTP POST callbacks when documents finish processing, batch
jobs complete, or errors occur.
"""
import logging
import threading
from datetime import datetime, timezone
from typing import Optional, Dict, Any

import requests

logger = logging.getLogger(__name__)

# Recognised event types
EVENT_SCAN_COMPLETE = 'scan_complete'
EVENT_BATCH_COMPLETE = 'batch_complete'
EVENT_SCAN_ERROR = 'scan_error'


def send_webhook(event_type: str, payload: Dict[str, Any],
                 webhook_url: str, timeout: int = 5,
                 async_send: bool = True) -> bool:
    """Deliver a webhook notification.

    Args:
        event_type: One of the ``EVENT_*`` constants.
        payload: Arbitrary JSON-serialisable data to include.
        webhook_url: Destination URL.
        timeout: HTTP request timeout in seconds.
        async_send: If ``True``, send in a background thread so the
                    caller is not blocked.

    Returns:
        ``True`` if dispatched (or queued); the actual delivery may
        still fail asynchronously.
    """
    if not webhook_url:
        return False

    body = {
        'event': event_type,
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'data': payload,
    }

    if async_send:
        t = threading.Thread(target=_do_send, args=(webhook_url, body, timeout),
                             daemon=True)
        t.start()
        return True
    else:
        return _do_send(webhook_url, body, timeout)


def _do_send(url: str, body: Dict, timeout: int) -> bool:
    try:
        resp = requests.post(url, json=body, timeout=timeout,
                             headers={'Content-Type': 'application/json',
                                      'User-Agent': 'OCR-DocumentScanner-Webhook/1.0'})
        if resp.ok:
            logger.info("Webhook delivered to %s (status %s)", url, resp.status_code)
            return True
        else:
            logger.warning("Webhook to %s returned %s", url, resp.status_code)
            return False
    except requests.RequestException as exc:
        logger.warning("Webhook delivery failed for %s: %s", url, exc)
        return False
