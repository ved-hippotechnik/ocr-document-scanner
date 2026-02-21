"""
JWT utilities for authentication and authorization
"""
import jwt
import os
from datetime import datetime, timedelta, timezone
from functools import wraps
from flask import request, jsonify, current_app
from ..database import db, User, LoginAttempt

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
        self.access_token_expires = app.config.get('JWT_ACCESS_TOKEN_EXPIRES', timedelta(hours=24))
        self.refresh_token_expires = app.config.get('JWT_REFRESH_TOKEN_EXPIRES', timedelta(days=30))
    
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
    """Decorator to require valid API key"""
    @wraps(f)
    def decorated(*args, **kwargs):
        api_key = request.headers.get('X-API-Key')
        
        if not api_key:
            return jsonify({'error': 'API key is missing'}), 401
        
        # ApiKey functionality disabled temporarily - always return error
        return jsonify({'error': 'API key authentication temporarily disabled'}), 503
        # api_key_obj.user.increment_api_calls()
        # 
        # # Add current user to request context
        # request.current_user = api_key_obj.user
        # request.current_api_key = api_key_obj
        # 
        # return f(*args, **kwargs)
    
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
        api_key = request.headers.get('X-API-Key')
        # API key functionality temporarily disabled
        if api_key:
            return jsonify({'error': 'API key authentication temporarily disabled'}), 503
        
        return jsonify({'error': 'Authentication required'}), 401
    
    return decorated

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

def check_rate_limit(user, requests_per_minute=60):
    """Check if user has exceeded rate limit"""
    if hasattr(request, 'current_api_key'):
        # Use API key specific limits
        api_key = request.current_api_key
        # TODO: Implement rate limiting logic based on API key limits
        return True
    
    # Default rate limiting for JWT users
    # TODO: Implement rate limiting logic
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