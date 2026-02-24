"""
Authentication routes for user management
"""
from flask import Blueprint, request, jsonify, current_app
from datetime import datetime, timezone
from ..database import db, User, LoginAttempt
from .jwt_utils import (
    jwt_manager, token_required, admin_required,
    log_login_attempt, is_account_locked
)
from ..validation import validate_email, validate_password
from ..rate_limiter import ratelimit_auth

auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')

@auth_bp.route('/register', methods=['POST'])
@ratelimit_auth()
def register():
    """
    Register a new user account.
    ---
    tags:
      - Authentication
    operationId: registerUser
    summary: Create a new user account
    description: >
      Creates a user account and returns a JWT access token plus a refresh
      token on success.  Passwords must be at least 8 characters and include
      a mix of uppercase letters, lowercase letters, digits, and at least one
      special character.

      **Rate limit**: 5 requests / minute per IP.
    parameters:
      - in: body
        name: body
        required: true
        schema:
          $ref: '#/definitions/RegisterRequest'
    responses:
      201:
        description: User registered successfully.
        schema:
          $ref: '#/definitions/AuthResponse'
      400:
        description: >
          Validation error — missing required fields, invalid email format,
          or password does not meet strength requirements.
        schema:
          $ref: '#/definitions/ErrorResponse'
        examples:
          application/json:
            error: Invalid email format
      409:
        description: Email address or username is already in use.
        schema:
          $ref: '#/definitions/ErrorResponse'
        examples:
          application/json:
            error: Email already registered
      429:
        description: Rate limit exceeded.
        schema:
          $ref: '#/definitions/ErrorResponse'
      500:
        description: Internal server error.
        schema:
          $ref: '#/definitions/ErrorResponse'
    """
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
        password_validation = validate_password(password, username=username)
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
        import traceback
        current_app.logger.error(f"Registration error: {e}\n{traceback.format_exc()}")
        return jsonify({'error': 'Registration failed'}), 500

@auth_bp.route('/login', methods=['POST'])
@ratelimit_auth()
def login():
    """
    Authenticate a user and receive JWT tokens.
    ---
    tags:
      - Authentication
    operationId: loginUser
    summary: Log in and receive JWT access and refresh tokens
    description: >
      Validates the provided credentials and returns a short-lived access
      token (default: 24 h) and a long-lived refresh token (default: 30 days).
      Include the access token on protected endpoints as:

      ```
      Authorization: Bearer <access_token>
      ```

      Accounts are temporarily locked (HTTP 423) after 5 consecutive failed
      login attempts from the same email address.

      **Rate limit**: 5 requests / minute per IP.
    parameters:
      - in: body
        name: body
        required: true
        schema:
          $ref: '#/definitions/LoginRequest'
    responses:
      200:
        description: Login successful — tokens returned.
        schema:
          $ref: '#/definitions/AuthResponse'
      400:
        description: Email or password field missing from request body.
        schema:
          $ref: '#/definitions/ErrorResponse'
        examples:
          application/json:
            error: Email and password are required
      401:
        description: Invalid credentials or account deactivated.
        schema:
          $ref: '#/definitions/ErrorResponse'
        examples:
          application/json:
            error: Invalid credentials
      423:
        description: Account temporarily locked after repeated failed attempts.
        schema:
          $ref: '#/definitions/ErrorResponse'
        examples:
          application/json:
            error: Account temporarily locked due to multiple failed login attempts
      429:
        description: Rate limit exceeded.
        schema:
          $ref: '#/definitions/ErrorResponse'
      500:
        description: Internal server error.
        schema:
          $ref: '#/definitions/ErrorResponse'
    """
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
        import traceback
        current_app.logger.error(f"Login error: {e}\n{traceback.format_exc()}")
        return jsonify({'error': 'Login failed'}), 500

@auth_bp.route('/refresh', methods=['POST'])
@ratelimit_auth()
def refresh():
    """
    Exchange a refresh token for a new access token.
    ---
    tags:
      - Authentication
    operationId: refreshToken
    summary: Refresh an expired access token
    description: >
      Present a valid refresh token to receive a fresh access token without
      requiring the user to log in again.  The refresh token itself is not
      rotated by this endpoint.
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          required:
            - refresh_token
          properties:
            refresh_token:
              type: string
              example: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
    responses:
      200:
        description: New access token issued.
        schema:
          type: object
          properties:
            access_token:
              type: string
              example: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
            expires_in:
              type: integer
              description: Token lifetime in seconds.
              example: 86400
      400:
        description: Refresh token missing from request body.
        schema:
          $ref: '#/definitions/ErrorResponse'
      401:
        description: Refresh token is invalid or has expired.
        schema:
          $ref: '#/definitions/ErrorResponse'
      500:
        description: Internal server error.
        schema:
          $ref: '#/definitions/ErrorResponse'
    """
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
        import traceback
        current_app.logger.error(f"Token refresh error: {e}\n{traceback.format_exc()}")
        return jsonify({'error': 'Token refresh failed'}), 500

@auth_bp.route('/profile', methods=['GET'])
@token_required
def get_profile():
    """
    Retrieve the authenticated user's profile.
    ---
    tags:
      - Authentication
    operationId: getUserProfile
    summary: Get current user profile
    description: >
      Returns the profile for the user identified by the JWT Bearer token
      supplied in the Authorization header.

      **Authentication**: JWT Bearer token required.
    security:
      - BearerAuth: []
    responses:
      200:
        description: Profile retrieved successfully.
        schema:
          type: object
          properties:
            user:
              $ref: '#/definitions/UserObject'
      401:
        description: Missing or invalid JWT token.
        schema:
          $ref: '#/definitions/ErrorResponse'
      500:
        description: Internal server error.
        schema:
          $ref: '#/definitions/ErrorResponse'
    """
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
@ratelimit_auth()
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

@auth_bp.route('/api-keys', methods=['GET', 'POST'])
@auth_bp.route('/api-keys/<key_id>', methods=['DELETE'])
@token_required
def api_keys_stub(key_id=None):
    """API key management — not yet implemented"""
    return jsonify({'error': 'API key functionality is not available'}), 503

@auth_bp.route('/forgot-password', methods=['POST'])
@ratelimit_auth()
def forgot_password():
    """Request password reset — not yet implemented (needs email service)"""
    return jsonify({'error': 'Password reset functionality is not yet available'}), 503

@auth_bp.route('/reset-password', methods=['POST'])
@ratelimit_auth()
def reset_password():
    """Reset password using token — not yet implemented"""
    return jsonify({'error': 'Password reset functionality is not yet available'}), 503

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