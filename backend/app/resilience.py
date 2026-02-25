"""
Production resilience utilities: timeouts, idempotency, backpressure, structured errors, operation tracking.

Usage:
    from .resilience import with_timeout, idempotent, backpressure, structured_error, track_operation

These decorators answer:
    Q1 (services down)  — with_timeout
    Q2 (1000 req/s)     — backpressure
    Q3 (slow network)   — with_timeout
    Q5 (aggressive retry)— idempotent
    Q6 (3AM debugging)  — structured_error
    Q7 (metrics)        — track_operation
"""

import time
import uuid
import signal
import logging
import threading
from functools import wraps
from datetime import datetime, timezone

from flask import request, g, jsonify, current_app
from prometheus_client import Counter, Histogram

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Prometheus metrics for resilience utilities
# ---------------------------------------------------------------------------
idempotent_cache_hits = Counter(
    'idempotent_cache_hits_total',
    'Number of idempotent cache hits (duplicate requests served from cache)',
    ['endpoint'],
)

backpressure_rejections = Counter(
    'backpressure_rejections_total',
    'Number of requests rejected due to backpressure',
    ['endpoint'],
)

operation_duration = Histogram(
    'tracked_operation_duration_seconds',
    'Duration of tracked operations',
    ['operation', 'status'],
)

timeout_events = Counter(
    'operation_timeout_total',
    'Number of timeout events',
    ['operation'],
)


# ---------------------------------------------------------------------------
# structured_error — consistent error responses with full debug context (Q6)
# ---------------------------------------------------------------------------
def structured_error(message, code, status_code=500, details=None, component=None):
    """
    Build a JSON error response with full debug context.

    Always includes:
    - request_id (from g.request_id, set by middleware in __init__.py)
    - error_id  (unique per error occurrence)
    - timestamp
    - component name
    - original error details (redacted in production unless debug mode)

    Returns (response_dict, status_code) tuple suitable for Flask route returns.
    """
    error_id = f"ERR-{uuid.uuid4().hex[:8].upper()}"
    request_id = getattr(g, 'request_id', 'unknown')

    body = {
        'error': message,
        'code': code,
        'error_id': error_id,
        'request_id': request_id,
        'timestamp': datetime.now(timezone.utc).isoformat(),
    }

    if component:
        body['component'] = component

    if details is not None:
        if current_app.debug:
            body['details'] = str(details)
        else:
            # In production, log details server-side but don't expose to client
            logger.error(
                "Error details for %s (request=%s): %s",
                error_id, request_id, details,
            )

    response = jsonify(body)
    response.headers['X-Error-ID'] = error_id
    response.headers['X-Request-ID'] = request_id

    if status_code == 503:
        response.headers['Retry-After'] = '30'

    return response, status_code


# ---------------------------------------------------------------------------
# @with_timeout — wraps a function with a hard timeout (Q1, Q3)
# ---------------------------------------------------------------------------
class _TimeoutError(Exception):
    """Raised when a function exceeds its allowed execution time."""
    pass


def with_timeout(seconds):
    """
    Decorator that enforces a wall-clock timeout on a function.

    Uses threading.Timer for cross-platform compatibility (signal.alarm
    only works on the main thread of Unix systems).

    On timeout, raises _TimeoutError which should be caught by the caller.
    """
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            result = [None]
            exception = [None]
            finished = threading.Event()

            def target():
                try:
                    result[0] = f(*args, **kwargs)
                except Exception as e:
                    exception[0] = e
                finally:
                    finished.set()

            thread = threading.Thread(target=target, daemon=True)
            thread.start()

            if not finished.wait(timeout=seconds):
                operation_name = f.__name__
                timeout_events.labels(operation=operation_name).inc()
                logger.error(
                    "Timeout after %ds in %s (request_id=%s)",
                    seconds, operation_name,
                    getattr(g, 'request_id', 'unknown'),
                )
                raise _TimeoutError(
                    f"Operation '{operation_name}' timed out after {seconds}s"
                )

            if exception[0] is not None:
                raise exception[0]

            return result[0]

        return wrapper
    return decorator


# ---------------------------------------------------------------------------
# @idempotent — cache responses for duplicate requests (Q5)
# ---------------------------------------------------------------------------
def idempotent(key_fn=None, ttl=300):
    """
    Decorator that makes an endpoint idempotent.

    If the request contains an X-Idempotency-Key header, the first response
    is cached. Subsequent requests with the same key return the cached
    response without re-executing the handler.

    Args:
        key_fn: Optional callable that extracts a custom idempotency key.
                Defaults to reading the X-Idempotency-Key header.
        ttl:    Cache TTL in seconds (default 5 minutes).
    """
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            # Extract idempotency key
            if key_fn:
                idem_key = key_fn()
            else:
                idem_key = request.headers.get('X-Idempotency-Key')

            if not idem_key:
                # No idempotency key → execute normally
                return f(*args, **kwargs)

            cache_key = f"idempotent:{request.path}:{idem_key}"

            # Check cache
            cache = getattr(current_app, 'cache', None)
            if cache:
                cached = cache.get(cache_key)
                if cached is not None:
                    endpoint = request.endpoint or 'unknown'
                    idempotent_cache_hits.labels(endpoint=endpoint).inc()
                    logger.info(
                        "Idempotent cache hit for key=%s endpoint=%s request_id=%s",
                        idem_key, endpoint, getattr(g, 'request_id', 'unknown'),
                    )
                    return jsonify(cached['body']), cached['status']

            # Execute the handler
            result = f(*args, **kwargs)

            # Cache the result
            if cache:
                if isinstance(result, tuple):
                    response_body, status_code = result
                    # Handle both dict and Response objects
                    if hasattr(response_body, 'get_json'):
                        body = response_body.get_json()
                    elif isinstance(response_body, dict):
                        body = response_body
                    else:
                        body = None

                    if body is not None:
                        cache.set(cache_key, {
                            'body': body,
                            'status': status_code,
                            'cached_at': datetime.now(timezone.utc).isoformat(),
                        }, ttl=ttl)

            return result

        return wrapper
    return decorator


# ---------------------------------------------------------------------------
# @backpressure — concurrency limiter (Q2)
# ---------------------------------------------------------------------------
_backpressure_semaphores = {}
_backpressure_lock = threading.Lock()


def backpressure(max_concurrent=20):
    """
    Decorator that limits concurrent executions of an endpoint.

    When max_concurrent is reached, returns 503 Service Unavailable
    with a Retry-After header instead of queueing.

    This prevents thread pool exhaustion and cascading failures
    under high load.
    """
    def decorator(f):
        # Create a semaphore per decorated function
        func_key = f"{f.__module__}.{f.__qualname__}"
        with _backpressure_lock:
            if func_key not in _backpressure_semaphores:
                _backpressure_semaphores[func_key] = threading.Semaphore(max_concurrent)

        @wraps(f)
        def wrapper(*args, **kwargs):
            sem = _backpressure_semaphores[func_key]

            acquired = sem.acquire(blocking=False)
            if not acquired:
                endpoint = request.endpoint or 'unknown'
                backpressure_rejections.labels(endpoint=endpoint).inc()
                logger.warning(
                    "Backpressure: rejecting request to %s — %d concurrent limit reached (request_id=%s)",
                    endpoint, max_concurrent, getattr(g, 'request_id', 'unknown'),
                )
                return structured_error(
                    message='Service temporarily overloaded',
                    code='BACKPRESSURE',
                    status_code=503,
                    component=endpoint,
                )

            try:
                return f(*args, **kwargs)
            finally:
                sem.release()

        return wrapper
    return decorator


# ---------------------------------------------------------------------------
# @track_operation — Prometheus timing + success/failure counters (Q7)
# ---------------------------------------------------------------------------
def track_operation(operation_name):
    """
    Decorator that records operation duration and outcome in Prometheus.

    Emits:
    - tracked_operation_duration_seconds{operation, status} histogram
    - Logs the operation with timing on completion

    Usage:
        @track_operation('ocr_scan')
        def scan_document():
            ...
    """
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            start = time.time()
            status = 'success'
            try:
                result = f(*args, **kwargs)
                return result
            except Exception as e:
                status = 'error'
                raise
            finally:
                duration = time.time() - start
                operation_duration.labels(
                    operation=operation_name,
                    status=status,
                ).observe(duration)

                if duration > 5.0:
                    logger.warning(
                        "Slow operation: %s took %.2fs (request_id=%s)",
                        operation_name, duration,
                        getattr(g, 'request_id', 'unknown'),
                    )

        return wrapper
    return decorator


# Re-export TimeoutError for route handlers to catch
TimeoutError = _TimeoutError
