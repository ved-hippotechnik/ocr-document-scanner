"""
Rate limiting configuration for the OCR Scanner API
"""

from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask import request, current_app
import logging
from functools import wraps
from typing import Optional, Callable

logger = logging.getLogger(__name__)

# Global limiter instance
limiter = None

def init_rate_limiter(app):
    """Initialize the rate limiter with the Flask app"""
    global limiter
    
    # Get storage URI - use Redis in production
    storage_uri = app.config.get('RATE_LIMIT_STORAGE_URL')
    if not storage_uri:
        if app.config.get('FLASK_ENV') == 'production':
            # Use Redis in production
            redis_url = app.config.get('REDIS_URL', 'redis://localhost:6379/1')
            storage_uri = redis_url
            logger.info(f"Using Redis for rate limiting: {redis_url.split('@')[-1]}")
        else:
            # Use memory storage in development
            storage_uri = 'memory://'
            logger.info("Using memory storage for rate limiting")
    
    # Configure rate limiter with more reasonable limits
    if app.config.get('FLASK_ENV') == 'production':
        default_limits = ["5000 per day", "500 per hour", "100 per minute"]
    else:
        # More generous limits for development
        default_limits = ["50000 per day", "10000 per hour", "1000 per minute"]
    
    limiter = Limiter(
        app=app,
        key_func=get_user_identifier,
        default_limits=default_limits,
        storage_uri=storage_uri,
        headers_enabled=True,  # Enable rate limit headers in responses
        swallow_errors=False,  # Don't swallow errors in production
        enabled=app.config.get('RATE_LIMIT_ENABLED', True),
        strategy='fixed-window',  # Use fixed window strategy
        key_prefix='rl:'  # Redis key prefix
    )
    
    # Configure error handlers
    limiter.request_filter(lambda: request.method == "OPTIONS")  # Don't count OPTIONS requests
    
    # Set up error handler for rate limit exceeded
    @app.errorhandler(429)
    def ratelimit_handler(e):
        return {
            'error': 'Rate limit exceeded',
            'message': str(e.description),
            'retry_after': e.retry_after if hasattr(e, 'retry_after') else None
        }, 429
    
    logger.info("✅ Rate limiter initialized with storage: %s", storage_uri.split('://')[0])
    return limiter

def get_user_identifier() -> str:
    """
    Get a unique identifier for the current user/request
    Priority: JWT user ID > API key > IP address
    """
    # Try to get user from JWT token
    try:
        from .auth.jwt_utils import get_current_user
        user = get_current_user()
        if user:
            return f"user:{user.id}"
    except:
        pass
    
    # Try to get API key from headers
    api_key = request.headers.get('X-API-Key')
    if api_key:
        return f"api_key:{api_key}"
    
    # Fall back to IP address
    return get_remote_address()

# Decorators for common rate limits
def ratelimit_light(per_minute: int = 30):
    """Light rate limit for non-intensive endpoints"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if limiter:
                return limiter.limit(f"{per_minute} per minute")(f)(*args, **kwargs)
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def ratelimit_medium(per_minute: int = 10):
    """Medium rate limit for standard endpoints"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if limiter:
                return limiter.limit(f"{per_minute} per minute")(f)(*args, **kwargs)
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def ratelimit_heavy(per_minute: int = 5):
    """Heavy rate limit for resource-intensive endpoints"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if limiter:
                return limiter.limit(f"{per_minute} per minute")(f)(*args, **kwargs)
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def ratelimit_scan():
    """Special rate limit for scan endpoints"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if limiter:
                return limiter.limit("2 per second, 20 per minute, 100 per hour")(f)(*args, **kwargs)
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def ratelimit_batch():
    """Special rate limit for batch processing"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if limiter:
                return limiter.limit("1 per second, 5 per minute, 20 per hour")(f)(*args, **kwargs)
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def ratelimit_auth():
    """Special rate limit for authentication endpoints"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if limiter:
                return limiter.limit("5 per minute, 20 per hour")(f)(*args, **kwargs)
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def ratelimit_analytics():
    """Rate limit for analytics endpoints"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if limiter:
                return limiter.limit("10 per minute, 100 per hour")(f)(*args, **kwargs)
            return f(*args, **kwargs)
        return decorated_function
    return decorator

# Custom rate limit decorator with dynamic limits
def dynamic_rate_limit(limit_func: Callable[[], str]):
    """
    Dynamic rate limiting based on user tier or other factors
    
    Args:
        limit_func: Function that returns a rate limit string
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            limit = limit_func()
            return limiter.limit(limit)(f)(*args, **kwargs)
        return decorated_function
    return decorator

# User tier-based rate limits
def get_user_tier_limit() -> str:
    """Get rate limit based on user tier"""
    try:
        from .auth.jwt_utils import get_current_user
        user = get_current_user()
        if user:
            if hasattr(user, 'tier'):
                if user.tier == 'premium':
                    return "100 per minute"
                elif user.tier == 'enterprise':
                    return "500 per minute"
    except:
        pass
    
    # Default tier
    return "20 per minute"

# Utility functions
def get_rate_limit_status():
    """Get current rate limit status for the request"""
    if not limiter:
        return None
    
    try:
        key = get_user_identifier()
        # This would need Redis or another backend to properly track
        return {
            'identifier': key,
            'limits': limiter.current_limits,
            'enabled': limiter.enabled
        }
    except Exception as e:
        logger.error(f"Error getting rate limit status: {e}")
        return None

def reset_rate_limits_for_user(user_id: int):
    """Reset rate limits for a specific user (admin function)"""
    if not limiter:
        return False
    
    try:
        key = f"user:{user_id}"
        # This would need Redis or another backend to properly reset
        logger.info(f"Rate limits reset for user {user_id}")
        return True
    except Exception as e:
        logger.error(f"Error resetting rate limits: {e}")
        return False

# Rate limit groups for different API sections
class RateLimitGroups:
    """Predefined rate limit groups for different API sections"""
    
    # Public endpoints (no auth required)
    PUBLIC = "5 per minute, 50 per hour"
    
    # Authenticated user endpoints
    USER = "20 per minute, 200 per hour"
    
    # Premium user endpoints
    PREMIUM = "50 per minute, 500 per hour"
    
    # Admin endpoints
    ADMIN = "100 per minute, 1000 per hour"
    
    # OCR processing endpoints
    OCR = "10 per minute, 60 per hour"
    
    # Batch processing endpoints
    BATCH = "5 per minute, 20 per hour"
    
    # Analytics endpoints
    ANALYTICS = "30 per minute, 300 per hour"
    
    # Health check endpoints (very permissive)
    HEALTH = "60 per minute"

# Error messages
RATE_LIMIT_MESSAGES = {
    'default': 'Rate limit exceeded. Please try again later.',
    'scan': 'Too many scan requests. Please wait before scanning more documents.',
    'batch': 'Batch processing limit reached. Please wait before submitting more batches.',
    'auth': 'Too many authentication attempts. Please wait before trying again.',
    'analytics': 'Analytics request limit reached. Please try again later.'
}

def ratelimit_adaptive(normal_limit: str = "20 per minute"):
    """Adaptive rate limiter that tightens under CPU pressure.

    - CPU < 75%: ``normal_limit``
    - 75-90%: halved
    - > 90%: quartered
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not limiter:
                return f(*args, **kwargs)
            try:
                import psutil
                cpu = psutil.cpu_percent(interval=0)
            except Exception:
                cpu = 0.0

            # Parse the numeric portion of the limit string (e.g. "20 per minute")
            parts = normal_limit.split()
            try:
                base = int(parts[0])
            except (IndexError, ValueError):
                base = 20
            suffix = " ".join(parts[1:]) or "per minute"

            if cpu > 90:
                effective = max(1, base // 4)
            elif cpu > 75:
                effective = max(1, base // 2)
            else:
                effective = base

            return limiter.limit(f"{effective} {suffix}")(f)(*args, **kwargs)
        return decorated_function
    return decorator


def get_rate_limit_message(endpoint_type: str = 'default') -> str:
    """Get appropriate rate limit message for endpoint type"""
    return RATE_LIMIT_MESSAGES.get(endpoint_type, RATE_LIMIT_MESSAGES['default'])