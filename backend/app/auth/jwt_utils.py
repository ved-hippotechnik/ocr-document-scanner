"""
JWT utilities for authentication and authorization
"""
import jwt
import os
from datetime import datetime, timedelta, timezone
from functools import wraps
from flask import request, jsonify, current_app
from ..database import db, User, LoginAttempt, ApiKey

class JWTManager:
    """JWT token management"""
    
    def __init__(self, app=None):
        self.app = app
        if app:
            self.init_app(app)
    
    def init_app(self, app):
        """Initialize JWT manager with Flask app"""
        self.app = app
        self.secret_key = app.config.get('JWT_SECRET_KEY', app.secret_key)
        self.algorithm = app.config.get('JWT_ALGORITHM', 'HS256')
        access_expires = app.config.get('JWT_ACCESS_TOKEN_EXPIRES', timedelta(hours=24))
        refresh_expires = app.config.get('JWT_REFRESH_TOKEN_EXPIRES', timedelta(days=30))
        # Convert int (seconds) to timedelta if needed
        self.access_token_expires = timedelta(seconds=access_expires) if isinstance(access_expires, (int, float)) else access_expires
        self.refresh_token_expires = timedelta(seconds=refresh_expires) if isinstance(refresh_expires, (int, float)) else refresh_expires
    
    def generate_tokens(self, user):
        """Generate access and refresh tokens for user"""
        now = datetime.now(timezone.utc)
        
        # Access token payload
        access_payload = {
            'user_id': str(user.id),
            'username': user.username,
            'email': user.email,
            'role': user.role,
            'iat': now,
            'exp': now + self.access_token_expires,
            'type': 'access'
        }
        
        # Refresh token payload
        refresh_payload = {
            'user_id': str(user.id),
            'iat': now,
            'exp': now + self.refresh_token_expires,
            'type': 'refresh'
        }
        
        access_token = jwt.encode(access_payload, self.secret_key, algorithm=self.algorithm)
        refresh_token = jwt.encode(refresh_payload, self.secret_key, algorithm=self.algorithm)
        
        return {
            'access_token': access_token,
            'refresh_token': refresh_token,
            'token_type': 'Bearer',
            'expires_in': int(self.access_token_expires.total_seconds())
        }
    
    def decode_token(self, token):
        """Decode and validate JWT token"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return payload
        except jwt.ExpiredSignatureError:
            return {'error': 'Token has expired'}
        except jwt.InvalidTokenError:
            return {'error': 'Invalid token'}
    
    def refresh_access_token(self, refresh_token):
        """Generate new access token from refresh token"""
        payload = self.decode_token(refresh_token)
        
        if 'error' in payload:
            return payload
        
        if payload.get('type') != 'refresh':
            return {'error': 'Invalid token type'}
        
        user = User.query.get(payload['user_id'])
        if not user or not user.is_active:
            return {'error': 'User not found or inactive'}
        
        return self.generate_tokens(user)

# Global JWT manager instance
jwt_manager = JWTManager()

def token_required(f):
    """Decorator to require valid JWT token"""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        auth_header = request.headers.get('Authorization')
        
        if auth_header:
            try:
                token = auth_header.split(' ')[1]  # Bearer <token>
            except IndexError:
                return jsonify({'error': 'Invalid authorization header format'}), 401
        
        if not token:
            return jsonify({'error': 'Token is missing'}), 401
        
        payload = jwt_manager.decode_token(token)
        
        if 'error' in payload:
            return jsonify(payload), 401
        
        if payload.get('type') != 'access':
            return jsonify({'error': 'Invalid token type'}), 401
        
        current_user = User.query.get(payload['user_id'])
        if not current_user or not current_user.is_active:
            return jsonify({'error': 'User not found or inactive'}), 401
        
        # Add current user to request context
        request.current_user = current_user
        return f(*args, **kwargs)
    
    return decorated

def api_key_required(f):
    """Decorator to require valid API key via X-API-Key header"""
    @wraps(f)
    def decorated(*args, **kwargs):
        raw_key = request.headers.get('X-API-Key')

        if not raw_key:
            return jsonify({'error': 'API key is missing'}), 401

        api_key_obj = ApiKey.verify(raw_key)
        if api_key_obj is None:
            return jsonify({'error': 'Invalid or expired API key'}), 401

        # Per-key rate limiting
        if not check_rate_limit(api_key_obj.user, requests_per_minute=api_key_obj.rate_limit):
            return jsonify({'error': 'Rate limit exceeded'}), 429

        request.current_user = api_key_obj.user
        request.current_api_key = api_key_obj
        return f(*args, **kwargs)

    return decorated

def token_or_api_key_required(f):
    """Decorator to require either JWT token or API key"""
    @wraps(f)
    def decorated(*args, **kwargs):
        # Try JWT token first
        auth_header = request.headers.get('Authorization')
        if auth_header:
            try:
                token = auth_header.split(' ')[1]
                payload = jwt_manager.decode_token(token)

                if 'error' not in payload and payload.get('type') == 'access':
                    current_user = User.query.get(payload['user_id'])
                    if current_user and current_user.is_active:
                        request.current_user = current_user
                        return f(*args, **kwargs)
            except (IndexError, Exception):
                pass

        # Try API key
        raw_key = request.headers.get('X-API-Key')
        if raw_key:
            api_key_obj = ApiKey.verify(raw_key)
            if api_key_obj is None:
                return jsonify({'error': 'Invalid or expired API key'}), 401

            if not check_rate_limit(api_key_obj.user, requests_per_minute=api_key_obj.rate_limit):
                return jsonify({'error': 'Rate limit exceeded'}), 429

            request.current_user = api_key_obj.user
            request.current_api_key = api_key_obj
            return f(*args, **kwargs)

        return jsonify({'error': 'Authentication required'}), 401

    return decorated

def scope_required(required_scope):
    """Decorator to require a specific API key scope (use after api_key_required)"""
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            api_key_obj = getattr(request, 'current_api_key', None)
            # JWT users bypass scope checks
            if api_key_obj is None:
                return f(*args, **kwargs)
            if not api_key_obj.has_scope(required_scope):
                return jsonify({'error': f'API key missing required scope: {required_scope}'}), 403
            return f(*args, **kwargs)
        return decorated
    return decorator

def admin_required(f):
    """Decorator to require admin role"""
    @wraps(f)
    def decorated(*args, **kwargs):
        if not hasattr(request, 'current_user') or not request.current_user.is_admin():
            return jsonify({'error': 'Admin access required'}), 403
        return f(*args, **kwargs)
    
    return decorated

def role_required(required_roles):
    """Decorator to require specific roles"""
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            if not hasattr(request, 'current_user'):
                return jsonify({'error': 'Authentication required'}), 401
            
            user_role = request.current_user.role
            if user_role not in required_roles:
                return jsonify({'error': 'Insufficient permissions'}), 403
            
            return f(*args, **kwargs)
        return decorated
    return decorator

_rate_limit_store = {}  # {key: [timestamp, ...]}
_rate_limit_prune_counter = 0


def check_rate_limit(user, requests_per_minute=60):
    """Check if user has exceeded rate limit using in-memory sliding window.

    Returns True if the request is allowed, False if rate-limited.
    """
    global _rate_limit_prune_counter
    import time

    now = time.time()
    window = 60  # 1 minute window

    api_key_obj = getattr(request, 'current_api_key', None)
    if api_key_obj is not None:
        key = f"apikey:{api_key_obj.id}"
        limit = api_key_obj.rate_limit or requests_per_minute
    else:
        key = f"user:{user.id if hasattr(user, 'id') else user}"
        limit = requests_per_minute

    # Get or create the timestamp list for this key
    if key not in _rate_limit_store:
        _rate_limit_store[key] = []

    # Remove expired timestamps outside the window
    _rate_limit_store[key] = [ts for ts in _rate_limit_store[key] if ts > now - window]

    # Periodic cleanup: prune stale keys to prevent unbounded memory growth
    _rate_limit_prune_counter += 1
    if _rate_limit_prune_counter >= 500:
        _rate_limit_prune_counter = 0
        stale = [k for k, v in _rate_limit_store.items()
                 if not v or v[-1] < now - window * 2]
        for k in stale:
            del _rate_limit_store[k]

    if len(_rate_limit_store[key]) >= limit:
        return False

    _rate_limit_store[key].append(now)
    return True

def log_login_attempt(email, ip_address, user_agent, success):
    """Log login attempt"""
    try:
        attempt = LoginAttempt(
            email=email,
            ip_address=ip_address,
            user_agent=user_agent,
            success=success
        )
        db.session.add(attempt)
        db.session.commit()
    except Exception as e:
        current_app.logger.error(f"Failed to log login attempt: {e}")
        db.session.rollback()

def get_current_user():
    """Get current user from JWT token"""
    try:
        # In a real implementation, this would decode the JWT token
        # from the request headers and return the user object
        # For now, return a mock user for testing
        return {'id': 1, 'email': 'test@example.com', 'role': 'user'}
    except Exception:
        return None

def is_account_locked(email):
    """Check if account is locked due to failed login attempts"""
    return LoginAttempt.is_account_locked(email)