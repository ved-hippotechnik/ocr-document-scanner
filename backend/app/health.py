"""
Deep health checks for all external dependencies.

Each checker:
- Has its own timeout (prevents health endpoint itself from hanging)
- Returns structured result with response time
- Attempts auto-recovery where possible (e.g., Redis reconnection)

Usage:
    from .health import aggregate_health
    status, details = aggregate_health(app)
"""

import time
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed

logger = logging.getLogger(__name__)

# Maximum time for the entire health check to complete
HEALTH_CHECK_TOTAL_TIMEOUT = 10  # seconds


def _timed_check(name, check_fn, timeout=3):
    """Run a check function with timing, returning a structured result."""
    start = time.time()
    try:
        result = check_fn()
        elapsed = round((time.time() - start) * 1000, 1)
        return {
            'name': name,
            'status': 'healthy' if result else 'unhealthy',
            'response_time_ms': elapsed,
            'details': result if isinstance(result, dict) else None,
        }
    except Exception as e:
        elapsed = round((time.time() - start) * 1000, 1)
        logger.error("Health check '%s' failed after %.1fms: %s", name, elapsed, e)
        return {
            'name': name,
            'status': 'unhealthy',
            'response_time_ms': elapsed,
            'error': str(e),
        }


def check_database(app):
    """SELECT 1 on the database with a 3s timeout."""
    def _check():
        from .database import db
        from sqlalchemy import text
        with app.app_context():
            db.session.execute(text('SELECT 1'))
            db.session.rollback()  # Don't leave open transaction
            return True
    return _timed_check('database', _check, timeout=3)


def check_redis(app):
    """PING Redis. If previously down, attempt reconnection."""
    def _check():
        cache = getattr(app, 'cache', None)
        if cache is None:
            return {'available': False, 'reason': 'cache not configured'}

        # If cache is a memory cache, it's always "healthy"
        if hasattr(cache, 'cache') and not hasattr(cache, 'redis_cache'):
            return {'type': 'memory', 'available': True}

        # Try Redis
        redis_cache = getattr(cache, 'redis_cache', None) if hasattr(cache, 'redis_cache') else cache
        if hasattr(redis_cache, 'redis_client') and redis_cache.redis_client:
            try:
                redis_cache.redis_client.ping()
                redis_cache.is_available = True
                return {'type': 'redis', 'available': True}
            except Exception:
                redis_cache.is_available = False
                # Attempt reconnection
                try:
                    redis_cache._connect()
                    if redis_cache.is_available:
                        return {'type': 'redis', 'available': True, 'reconnected': True}
                except Exception:
                    pass
                return {'type': 'redis', 'available': False}
        elif hasattr(redis_cache, '_connect'):
            # Never connected, try now
            try:
                redis_cache._connect()
                return {'type': 'redis', 'available': redis_cache.is_available}
            except Exception:
                return {'type': 'redis', 'available': False}

        return {'type': 'unknown', 'available': True}

    return _timed_check('cache', _check, timeout=2)


def check_celery(app):
    """Ping Celery workers with a timeout."""
    def _check():
        celery = getattr(app, 'celery', None)
        if celery is None:
            return {'available': False, 'reason': 'celery not configured'}

        try:
            inspect = celery.control.inspect(timeout=3)
            ping_result = inspect.ping()
            if ping_result:
                worker_count = len(ping_result)
                return {'available': True, 'workers': worker_count}
            else:
                return {'available': False, 'workers': 0, 'reason': 'no workers responded'}
        except Exception as e:
            return {'available': False, 'error': str(e)}

    return _timed_check('celery', _check, timeout=5)


def check_tesseract(app):
    """Verify Tesseract OCR engine is accessible."""
    def _check():
        import pytesseract
        version = pytesseract.get_tesseract_version()
        return {'available': True, 'version': str(version)}

    return _timed_check('tesseract', _check, timeout=3)


def check_vision_service(app):
    """Check if Claude Vision service is configured and responsive."""
    def _check():
        vision = getattr(app, 'vision_service', None)
        if vision is None:
            return {'available': False, 'reason': 'not configured'}
        # Just verify the service object exists and has required attributes
        if hasattr(vision, 'client') and vision.client:
            return {'available': True, 'model': getattr(vision, 'model', 'unknown')}
        return {'available': False, 'reason': 'client not initialized'}

    return _timed_check('vision_service', _check, timeout=2)


def aggregate_health(app):
    """
    Run all health checks concurrently and aggregate results.

    Returns:
        tuple: (overall_status, details_dict)
        overall_status is one of: 'healthy', 'degraded', 'unhealthy'
    """
    checks = [
        ('database', lambda: check_database(app)),
        ('cache', lambda: check_redis(app)),
        ('celery', lambda: check_celery(app)),
        ('tesseract', lambda: check_tesseract(app)),
        ('vision_service', lambda: check_vision_service(app)),
    ]

    results = {}

    # Run checks concurrently with a total timeout
    with ThreadPoolExecutor(max_workers=len(checks)) as executor:
        futures = {
            executor.submit(check_fn): name
            for name, check_fn in checks
        }

        for future in as_completed(futures, timeout=HEALTH_CHECK_TOTAL_TIMEOUT):
            name = futures[future]
            try:
                results[name] = future.result()
            except Exception as e:
                results[name] = {
                    'name': name,
                    'status': 'unhealthy',
                    'error': f'Check timed out or failed: {e}',
                }

    # Determine overall status
    # Critical services: database, tesseract
    # Non-critical: cache, celery, vision_service
    critical_services = ['database', 'tesseract']
    non_critical_services = ['cache', 'celery', 'vision_service']

    critical_healthy = all(
        results.get(s, {}).get('status') == 'healthy'
        for s in critical_services
        if s in results
    )

    non_critical_healthy = all(
        results.get(s, {}).get('status') == 'healthy'
        for s in non_critical_services
        if s in results
    )

    if critical_healthy and non_critical_healthy:
        overall = 'healthy'
    elif critical_healthy:
        overall = 'degraded'
    else:
        overall = 'unhealthy'

    return overall, results
