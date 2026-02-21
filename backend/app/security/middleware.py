"""
Security middleware for request processing
"""
import time
import logging
from functools import wraps
from flask import request, jsonify, current_app, g
from typing import Optional, Callable

from .request_signing import security_hardening, verify_signed_request

logger = logging.getLogger(__name__)


def security_middleware():
    """
    Flask before_request handler for security checks
    """
    # Skip security checks for health, stats, and documents endpoints
    skip_endpoints = [
        'health_check', 
        'enhanced_v2.health_check', 
        'main.get_stats', 
        'main.get_documents',
        'main.get_scan_history',
        'enhanced_v2.get_stats'
    ]
    if request.endpoint in skip_endpoints:
        return None
    
    # Skip for OPTIONS requests (CORS preflight)
    if request.method == 'OPTIONS':
        return None
    
    # Get client IP
    client_ip = get_client_ip()
    g.client_ip = client_ip
    
    # 1. IP reputation check
    is_valid_ip, ip_error = security_hardening.check_ip_reputation(client_ip)
    if not is_valid_ip:
        logger.warning(f"IP reputation check failed for {client_ip}: {ip_error}")
        return jsonify({
            'error': 'Access denied',
            'code': 'IP_BLOCKED',
            'message': 'Your IP address has been blocked'
        }), 403
    
    # 2. Rate limiting
    rate_limit_key = f"ip:{client_ip}"
    is_within_limit, rate_error = security_hardening.apply_rate_limiting(
        rate_limit_key,
        limit=current_app.config.get('RATE_LIMIT_REQUESTS', 1000),
        window=current_app.config.get('RATE_LIMIT_WINDOW', 3600)
    )
    if not is_within_limit:
        logger.warning(f"Rate limit exceeded for {client_ip}: {rate_error}")
        return jsonify({
            'error': 'Rate limit exceeded',
            'code': 'RATE_LIMIT_EXCEEDED',
            'message': 'Too many requests. Please try again later.'
        }), 429
    
    # 3. Request size validation
    content_length = request.content_length or 0
    is_valid_size, size_error = security_hardening.validate_request_size(content_length)
    if not is_valid_size:
        logger.warning(f"Request size validation failed for {client_ip}: {size_error}")
        return jsonify({
            'error': 'Request too large',
            'code': 'REQUEST_TOO_LARGE',
            'message': 'Request payload exceeds maximum allowed size'
        }), 413
    
    # 4. Header validation
    is_valid_headers, header_error = security_hardening.validate_request_headers(dict(request.headers))
    if not is_valid_headers:
        logger.warning(f"Header validation failed for {client_ip}: {header_error}")
        return jsonify({
            'error': 'Invalid headers',
            'code': 'INVALID_HEADERS',
            'message': 'Request headers are invalid or missing'
        }), 400
    
    # 5. JSON payload validation (for JSON requests)
    if request.is_json and request.get_data():
        try:
            payload = request.get_data(as_text=True)
            is_valid_json, json_error, parsed_data = security_hardening.validate_json_payload(payload)
            if not is_valid_json:
                logger.warning(f"JSON validation failed for {client_ip}: {json_error}")
                return jsonify({
                    'error': 'Invalid JSON payload',
                    'code': 'INVALID_JSON',
                    'message': 'JSON payload is invalid or contains malicious content'
                }), 400
        except Exception as e:
            logger.error(f"JSON validation error for {client_ip}: {e}")
            return jsonify({
                'error': 'JSON processing error',
                'code': 'JSON_ERROR',
                'message': 'Unable to process JSON payload'
            }), 400
    
    # 6. Request signature validation (optional, enabled by config)
    if current_app.config.get('REQUIRE_REQUEST_SIGNING', False):
        is_valid_signature, sig_error = verify_signed_request()
        if not is_valid_signature:
            logger.warning(f"Signature validation failed for {client_ip}: {sig_error}")
            return jsonify({
                'error': 'Invalid request signature',
                'code': 'INVALID_SIGNATURE',
                'message': 'Request signature is invalid or missing'
            }), 401
    
    # Store security context for later use
    g.security_validated = True
    g.security_timestamp = time.time()
    
    return None


def get_client_ip() -> str:
    """Get the real client IP address"""
    # Check for various proxy headers
    possible_headers = [
        'X-Forwarded-For',
        'X-Real-IP',
        'X-Client-IP',
        'HTTP_X_FORWARDED_FOR',
        'HTTP_X_REAL_IP'
    ]
    
    for header in possible_headers:
        ip = request.headers.get(header)
        if ip:
            # X-Forwarded-For can contain multiple IPs, take the first one
            return ip.split(',')[0].strip()
    
    # Fallback to remote_addr
    return request.environ.get('REMOTE_ADDR', 'unknown')


def require_signature(f: Callable) -> Callable:
    """
    Decorator to require request signature for specific endpoints
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        is_valid, error = verify_signed_request()
        if not is_valid:
            logger.warning(f"Signature required but validation failed: {error}")
            return jsonify({
                'error': 'Signature required',
                'code': 'SIGNATURE_REQUIRED',
                'message': 'This endpoint requires a valid request signature'
            }), 401
        
        return f(*args, **kwargs)
    
    return decorated_function


def require_api_key(f: Callable) -> Callable:
    """
    Decorator to require API key for specific endpoints
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        api_key = request.headers.get('X-API-Key')
        
        if not api_key:
            return jsonify({
                'error': 'API key required',
                'code': 'API_KEY_REQUIRED',
                'message': 'X-API-Key header is required'
            }), 401
        
        # Validate API key (implement your validation logic)
        if not validate_api_key(api_key):
            return jsonify({
                'error': 'Invalid API key',
                'code': 'INVALID_API_KEY',
                'message': 'The provided API key is invalid'
            }), 401
        
        # Store API key info in g for later use
        g.api_key = api_key
        
        return f(*args, **kwargs)
    
    return decorated_function


def validate_api_key(api_key: str) -> bool:
    """
    Validate API key against configured keys
    """
    # Get valid API keys from config
    valid_keys = current_app.config.get('VALID_API_KEYS', [])
    
    if not valid_keys:
        # If no API keys configured, accept any non-empty key
        return bool(api_key.strip())
    
    return api_key in valid_keys


def enhanced_cors():
    """
    Enhanced CORS handling with security considerations
    """
    # Skip for non-CORS requests
    if 'Origin' not in request.headers:
        return None
    
    origin = request.headers.get('Origin')
    
    # Get allowed origins from config
    if current_app.config.get('FLASK_ENV') == 'production':
        # Strict CORS in production
        allowed_origins = current_app.config.get('CORS_ORIGINS', [])
        
        # Convert localhost references to production domains
        allowed_origins = [o for o in allowed_origins if 'localhost' not in o]
        
        if not allowed_origins:
            # No CORS allowed if not configured
            logger.warning(f"CORS: No allowed origins configured, blocking {origin}")
            return jsonify({
                'error': 'CORS not configured',
                'code': 'CORS_NOT_CONFIGURED'
            }), 403
        
        if origin not in allowed_origins:
            logger.warning(f"CORS: Blocked origin {origin}")
            return jsonify({
                'error': 'Origin not allowed',
                'code': 'CORS_ORIGIN_DENIED'
            }), 403
    else:
        # Development mode - more permissive but still controlled
        allowed_origins = current_app.config.get('CORS_ORIGINS', ['http://localhost:3000', 'http://localhost:3001'])
        
        if origin not in allowed_origins and not origin.startswith('http://localhost'):
            logger.warning(f"CORS: Blocked non-localhost origin in dev: {origin}")
            return jsonify({
                'error': 'Origin not allowed in development',
                'code': 'CORS_ORIGIN_DENIED'
            }), 403
    
    return None


def security_headers():
    """
    Add comprehensive security headers to responses
    """
    def add_security_headers(response):
        # Skip headers for certain responses
        if response.status_code >= 500:
            return response
        
        # Check if security headers are enabled
        if not current_app.config.get('SECURITY_HEADERS_ENABLED', True):
            return response
        
        # Prevent XSS attacks
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        
        # HSTS - configurable for production and development
        if current_app.config.get('FLASK_ENV') == 'production' or current_app.config.get('ENABLE_HSTS', False):
            # Use shorter duration for development, full duration for production
            if current_app.config.get('FLASK_ENV') == 'production':
                response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains; preload'
            else:
                response.headers['Strict-Transport-Security'] = 'max-age=86400; includeSubDomains'
        
        # Content Security Policy - configurable
        csp = current_app.config.get('CONTENT_SECURITY_POLICY')
        if not csp:
            # Default restrictive CSP
            if current_app.config.get('FLASK_ENV') == 'production':
                csp = (
                    "default-src 'self'; "
                    "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
                    "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
                    "font-src 'self' https://fonts.gstatic.com; "
                    "img-src 'self' data: https:; "
                    "connect-src 'self'; "
                    "frame-ancestors 'none'; "
                    "base-uri 'self'; "
                    "form-action 'self'"
                )
            else:
                # More permissive in development
                csp = (
                    "default-src 'self'; "
                    "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
                    "style-src 'self' 'unsafe-inline'; "
                    "img-src 'self' data: blob:; "
                    "connect-src 'self' ws: wss:"
                )
        response.headers['Content-Security-Policy'] = csp
        
        # Referrer Policy
        response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        
        # Permissions Policy (formerly Feature Policy)
        response.headers['Permissions-Policy'] = (
            'accelerometer=(), '
            'camera=(), '
            'geolocation=(), '
            'gyroscope=(), '
            'magnetometer=(), '
            'microphone=(), '
            'payment=(), '
            'usb=()'
        )
        
        # Additional security headers
        response.headers['X-Permitted-Cross-Domain-Policies'] = 'none'
        response.headers['X-Download-Options'] = 'noopen'
        
        # Remove server header in production
        if current_app.config.get('FLASK_ENV') == 'production':
            response.headers.pop('Server', None)
        
        # Cache control for sensitive content
        if request.path.startswith('/api/auth') or request.path.startswith('/api/user'):
            response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, private'
            response.headers['Pragma'] = 'no-cache'
            response.headers['Expires'] = '0'
        
        return response
    
    return add_security_headers


def setup_security_middleware(app):
    """
    Setup all security middleware for the Flask app
    """
    # Register before_request handlers
    app.before_request(security_middleware)
    app.before_request(enhanced_cors)
    
    # Register after_request handler for security headers
    app.after_request(security_headers())
    
    logger.info("Security middleware initialized")


class SecurityMetrics:
    """Track security-related metrics"""
    
    def __init__(self):
        self.blocked_requests = 0
        self.rate_limited_requests = 0
        self.signature_failures = 0
        self.malicious_payloads = 0
        
    def increment_blocked(self):
        self.blocked_requests += 1
        
    def increment_rate_limited(self):
        self.rate_limited_requests += 1
        
    def increment_signature_failures(self):
        self.signature_failures += 1
        
    def increment_malicious_payloads(self):
        self.malicious_payloads += 1
        
    def get_metrics(self) -> dict:
        return {
            'blocked_requests': self.blocked_requests,
            'rate_limited_requests': self.rate_limited_requests,
            'signature_failures': self.signature_failures,
            'malicious_payloads': self.malicious_payloads
        }


# Global security metrics instance
security_metrics = SecurityMetrics()