"""
Authentication routes for user management
"""
from flask import Blueprint, request, jsonify, current_app
from datetime import datetime, timedelta, timezone
import re
import secrets
from ..database import db, User, LoginAttempt
from .jwt_utils import (
    jwt_manager, token_required, admin_required, 
    log_login_attempt, is_account_locked
)
from ..validation import validate_email, validate_password, ProcessingError
from ..rate_limiter import ratelimit_auth, ratelimit_light

auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')

@auth_bp.route('/register', methods=['POST'])
@ratelimit_auth()
def register():
    """Register a new user"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['email', 'username', 'password']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'{field} is required'}), 400
        
        email = data['email'].lower().strip()
        username = data['username'].strip()
        password = data['password']
        
        # Validate email format
        if not validate_email(email):
            return jsonify({'error': 'Invalid email format'}), 400
        
        # Validate password strength
        password_validation = validate_password(password)
        if not password_validation['valid']:
            return jsonify({'error': password_validation['message']}), 400
        
        # Check if user already exists
        if User.query.filter_by(email=email).first():
            return jsonify({'error': 'Email already registered'}), 409
        
        if User.query.filter_by(username=username).first():
            return jsonify({'error': 'Username already taken'}), 409
        
        # Create new user
        user = User(
            email=email,
            username=username,
            first_name=data.get('first_name', '').strip(),
            last_name=data.get('last_name', '').strip(),
            organization=data.get('organization', '').strip(),
            # role=UserRole.USER
        )
        user.set_password(password)
        
        db.session.add(user)
        db.session.commit()
        
        # Generate tokens
        tokens = jwt_manager.generate_tokens(user)
        
        # Log successful registration
        log_login_attempt(
            email=email,
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent', ''),
            success=True
        )
        
        return jsonify({
            'message': 'User registered successfully',
            'user': user.to_dict(),
            **tokens
        }), 201
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Registration error: {e}")
        return jsonify({'error': 'Registration failed'}), 500

@auth_bp.route('/login', methods=['POST'])
@ratelimit_auth()
def login():
    """Authenticate user and return JWT tokens"""
    try:
        data = request.get_json()
        
        if not data.get('email') or not data.get('password'):
            return jsonify({'error': 'Email and password are required'}), 400
        
        email = data['email'].lower().strip()
        password = data['password']
        
        # Check if account is locked
        if is_account_locked(email):
            return jsonify({
                'error': 'Account temporarily locked due to multiple failed login attempts'
            }), 423
        
        # Find user
        user = User.query.filter_by(email=email).first()
        
        # Check credentials
        if not user or not user.check_password(password):
            log_login_attempt(
                email=email,
                ip_address=request.remote_addr,
                user_agent=request.headers.get('User-Agent', ''),
                success=False
            )
            return jsonify({'error': 'Invalid credentials'}), 401
        
        # Check if user is active
        if not user.is_active:
            return jsonify({'error': 'Account is deactivated'}), 401
        
        # Update last login
        user.last_login = datetime.now(timezone.utc)
        db.session.commit()
        
        # Generate tokens
        tokens = jwt_manager.generate_tokens(user)
        
        # Log successful login
        log_login_attempt(
            email=email,
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent', ''),
            success=True
        )
        
        return jsonify({
            'message': 'Login successful',
            'user': user.to_dict(),
            **tokens
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Login error: {e}")
        return jsonify({'error': 'Login failed'}), 500

@auth_bp.route('/refresh', methods=['POST'])
def refresh():
    """Refresh access token using refresh token"""
    try:
        data = request.get_json()
        refresh_token = data.get('refresh_token')
        
        if not refresh_token:
            return jsonify({'error': 'Refresh token is required'}), 400
        
        result = jwt_manager.refresh_access_token(refresh_token)
        
        if 'error' in result:
            return jsonify(result), 401
        
        return jsonify(result), 200
        
    except Exception as e:
        current_app.logger.error(f"Token refresh error: {e}")
        return jsonify({'error': 'Token refresh failed'}), 500

@auth_bp.route('/profile', methods=['GET'])
@token_required
def get_profile():
    """Get current user profile"""
    try:
        return jsonify({
            'user': request.current_user.to_dict()
        }), 200
    except Exception as e:
        current_app.logger.error(f"Profile error: {e}")
        return jsonify({'error': 'Failed to get profile'}), 500

@auth_bp.route('/profile', methods=['PUT'])
@token_required
def update_profile():
    """Update user profile"""
    try:
        data = request.get_json()
        user = request.current_user
        
        # Update allowed fields
        allowed_fields = ['first_name', 'last_name', 'organization']
        for field in allowed_fields:
            if field in data:
                setattr(user, field, data[field].strip() if data[field] else None)
        
        user.updated_at = datetime.now(timezone.utc)
        db.session.commit()
        
        return jsonify({
            'message': 'Profile updated successfully',
            'user': user.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Profile update error: {e}")
        return jsonify({'error': 'Profile update failed'}), 500

@auth_bp.route('/change-password', methods=['POST'])
@token_required
def change_password():
    """Change user password"""
    try:
        data = request.get_json()
        user = request.current_user
        
        current_password = data.get('current_password')
        new_password = data.get('new_password')
        
        if not current_password or not new_password:
            return jsonify({'error': 'Current and new passwords are required'}), 400
        
        # Verify current password
        if not user.check_password(current_password):
            return jsonify({'error': 'Current password is incorrect'}), 401
        
        # Validate new password
        password_validation = validate_password(new_password)
        if not password_validation['valid']:
            return jsonify({'error': password_validation['message']}), 400
        
        # Update password
        user.set_password(new_password)
        user.updated_at = datetime.now(timezone.utc)
        db.session.commit()
        
        return jsonify({'message': 'Password changed successfully'}), 200
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Password change error: {e}")
        return jsonify({'error': 'Password change failed'}), 500

@auth_bp.route('/api-keys', methods=['GET'])
@token_required
def get_api_keys():
    """Get user's API keys"""
    try:
        user = request.current_user
        api_keys = [key.to_dict() for key in user.api_keys if key.is_active]
        
        return jsonify({
            'api_keys': api_keys,
            'total': len(api_keys)
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"API keys error: {e}")
        return jsonify({'error': 'Failed to get API keys'}), 500

@auth_bp.route('/api-keys', methods=['POST'])
@token_required
def create_api_key():
    """Create new API key"""
    try:
        data = request.get_json()
        user = request.current_user
        
        name = data.get('name', '').strip()
        if not name:
            return jsonify({'error': 'API key name is required'}), 400
        
        # Check if user has too many API keys
        active_keys = len([key for key in user.api_keys if key.is_active])
        if active_keys >= 10:  # Limit to 10 API keys per user
            return jsonify({'error': 'Maximum API keys limit reached'}), 400
        
        # Generate new API key
        # ApiKey functionality temporarily disabled
        return jsonify({'error': 'API key functionality temporarily disabled'}), 503
        # api_key_value = ApiKey.generate_key()
        
        api_key = ApiKey(
            user_id=user.id,
            name=name,
            can_read=data.get('can_read', True),
            can_write=data.get('can_write', True),
            can_delete=data.get('can_delete', False),
            requests_per_minute=data.get('requests_per_minute', 60),
            requests_per_day=data.get('requests_per_day', 1000),
            expires_at=None  # No expiration by default
        )
        
        if data.get('expires_in_days'):
            api_key.expires_at = datetime.now(timezone.utc) + timedelta(days=data['expires_in_days'])
        
        api_key.set_key(api_key_value)
        
        db.session.add(api_key)
        db.session.commit()
        
        # Return the key value only once
        result = api_key.to_dict()
        result['key'] = api_key_value
        
        return jsonify({
            'message': 'API key created successfully',
            'api_key': result
        }), 201
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"API key creation error: {e}")
        return jsonify({'error': 'API key creation failed'}), 500

@auth_bp.route('/api-keys/<key_id>', methods=['DELETE'])
@token_required
def delete_api_key(key_id):
    """Delete API key"""
    try:
        user = request.current_user
        api_key = ApiKey.query.filter_by(id=key_id, user_id=user.id).first()
        
        if not api_key:
            return jsonify({'error': 'API key not found'}), 404
        
        api_key.is_active = False
        db.session.commit()
        
        return jsonify({'message': 'API key deleted successfully'}), 200
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"API key deletion error: {e}")
        return jsonify({'error': 'API key deletion failed'}), 500

@auth_bp.route('/forgot-password', methods=['POST'])
def forgot_password():
    """Request password reset"""
    try:
        data = request.get_json()
        email = data.get('email', '').lower().strip()
        
        if not email:
            return jsonify({'error': 'Email is required'}), 400
        
        user = User.query.filter_by(email=email).first()
        
        # Always return success to prevent email enumeration
        if user and user.is_active:
            # Generate reset token
            # Password reset functionality temporarily disabled
            return jsonify({'error': 'Password reset functionality temporarily disabled'}), 503
            # token = PasswordReset.generate_token()
            expires_at = datetime.now(timezone.utc) + timedelta(hours=1)
            
            reset = PasswordReset(
                user_id=user.id,
                token=token,
                expires_at=expires_at
            )
            
            db.session.add(reset)
            db.session.commit()
            
            # TODO: Send email with reset link
            current_app.logger.info(f"Password reset requested for {email}")
        
        return jsonify({
            'message': 'If the email exists, a password reset link has been sent'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Password reset request error: {e}")
        return jsonify({'error': 'Password reset request failed'}), 500

@auth_bp.route('/reset-password', methods=['POST'])
def reset_password():
    """Reset password using token"""
    try:
        data = request.get_json()
        token = data.get('token')
        new_password = data.get('new_password')
        
        if not token or not new_password:
            return jsonify({'error': 'Token and new password are required'}), 400
        
        # Find valid reset token
        reset = PasswordReset.query.filter_by(token=token).first()
        
        if not reset or not reset.is_valid():
            return jsonify({'error': 'Invalid or expired reset token'}), 400
        
        # Validate new password
        password_validation = validate_password(new_password)
        if not password_validation['valid']:
            return jsonify({'error': password_validation['message']}), 400
        
        # Update password
        user = reset.user
        user.set_password(new_password)
        user.updated_at = datetime.now(timezone.utc)
        
        # Mark token as used
        reset.mark_as_used()
        
        db.session.commit()
        
        return jsonify({'message': 'Password reset successfully'}), 200
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Password reset error: {e}")
        return jsonify({'error': 'Password reset failed'}), 500

# Admin routes
@auth_bp.route('/admin/users', methods=['GET'])
@token_required
@admin_required
def get_users():
    """Get all users (admin only)"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 20, type=int), 100)
        
        users = User.query.order_by(User.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        return jsonify({
            'users': [user.to_dict() for user in users.items],
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': users.total,
                'pages': users.pages,
                'has_next': users.has_next,
                'has_prev': users.has_prev
            }
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Get users error: {e}")
        return jsonify({'error': 'Failed to get users'}), 500

@auth_bp.route('/admin/users/<user_id>/deactivate', methods=['POST'])
@token_required
@admin_required
def deactivate_user(user_id):
    """Deactivate user (admin only)"""
    try:
        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        user.is_active = False
        user.updated_at = datetime.now(timezone.utc)
        db.session.commit()
        
        return jsonify({'message': 'User deactivated successfully'}), 200
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"User deactivation error: {e}")
        return jsonify({'error': 'User deactivation failed'}), 500

@auth_bp.route('/admin/users/<user_id>/activate', methods=['POST'])
@token_required
@admin_required
def activate_user(user_id):
    """Activate user (admin only)"""
    try:
        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        user.is_active = True
        user.updated_at = datetime.now(timezone.utc)
        db.session.commit()
        
        return jsonify({'message': 'User activated successfully'}), 200
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"User activation error: {e}")
        return jsonify({'error': 'User activation failed'}), 500