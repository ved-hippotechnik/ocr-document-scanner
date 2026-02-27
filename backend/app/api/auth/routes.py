"""
api/auth/routes.py
==================
Authentication endpoints — no version prefix (auth is never versioned).

Routes (url_prefix=/api/auth)
---------------------------------
POST /api/auth/register              — create a new user account
POST /api/auth/login                 — authenticate and receive tokens
POST /api/auth/refresh               — exchange refresh token for new access token
GET  /api/auth/profile               — get the current user's profile
PUT  /api/auth/profile               — update the current user's profile
POST /api/auth/change-password       — change the authenticated user's password
GET|POST /api/auth/api-keys          — API key management (stub: returns 503)
DELETE   /api/auth/api-keys/<key_id> — API key management (stub: returns 503)
POST /api/auth/forgot-password       — request password reset (stub: returns 503)
POST /api/auth/reset-password        — reset password via token (stub: returns 503)
GET  /api/auth/admin/users                         — list users (admin only)
POST /api/auth/admin/users/<user_id>/deactivate    — deactivate user (admin only)
POST /api/auth/admin/users/<user_id>/activate      — activate user (admin only)

This file is a copy of ``app/auth/routes.py`` re-homed under ``app/api/auth/``.
Import paths are updated to be absolute from the ``app`` package root so this
module works correctly whether imported from the old or the new location.

Authentication (for protected routes)
--------------------------------------
``@token_required`` — valid JWT Bearer token.
``@admin_required`` — additionally requires the ``admin`` role.
"""
from __future__ import annotations

import traceback
from datetime import datetime, timezone

from flask import Blueprint, current_app, jsonify, request

from app.auth.jwt_utils import (
    jwt_manager,
    token_required,
    admin_required,
    log_login_attempt,
    is_account_locked,
)
from app.database import db, User, LoginAttempt
from app.validation import validate_email, validate_password
from app.rate_limiter import ratelimit_auth

auth_v2_bp = Blueprint("auth_v2", __name__, url_prefix="/api/auth")


# ---------------------------------------------------------------------------
# Public endpoints
# ---------------------------------------------------------------------------

@auth_v2_bp.route("/register", methods=["POST"])
@ratelimit_auth()
def register():
    """
    Register a new user account.
    ---
    tags:
      - Authentication
    operationId: registerUserV2
    summary: Create a new user account
    description: >
      Creates a user account and returns a JWT access token plus a refresh
      token on success.  Passwords must be at least 8 characters with a mix
      of uppercase, lowercase, digits, and at least one special character.

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
      400:
        description: Validation error — missing fields, bad email, or weak password.
      409:
        description: Email or username already in use.
      429:
        description: Rate limit exceeded.
      500:
        description: Internal server error.
    """
    try:
        data = request.get_json()

        required_fields = ["email", "username", "password"]
        for field in required_fields:
            if not data.get(field):
                return jsonify({"error": f"{field} is required"}), 400

        email = data["email"].lower().strip()
        username = data["username"].strip()
        password = data["password"]

        if not validate_email(email):
            return jsonify({"error": "Invalid email format"}), 400

        password_validation = validate_password(password, username=username)
        if not password_validation["valid"]:
            return jsonify({"error": password_validation["message"]}), 400

        if User.query.filter_by(email=email).first():
            return jsonify({"error": "Email already registered"}), 409

        if User.query.filter_by(username=username).first():
            return jsonify({"error": "Username already taken"}), 409

        user = User(
            email=email,
            username=username,
            first_name=data.get("first_name", "").strip(),
            last_name=data.get("last_name", "").strip(),
            organization=data.get("organization", "").strip(),
        )
        user.set_password(password)
        db.session.add(user)
        db.session.commit()

        tokens = jwt_manager.generate_tokens(user)

        log_login_attempt(
            email=email,
            ip_address=request.remote_addr,
            user_agent=request.headers.get("User-Agent", ""),
            success=True,
        )

        return jsonify({
            "message": "User registered successfully",
            "user": user.to_dict(),
            **tokens,
        }), 201

    except Exception as exc:
        db.session.rollback()
        current_app.logger.error("Registration error: %s\n%s", exc, traceback.format_exc())
        return jsonify({"error": "Registration failed"}), 500


@auth_v2_bp.route("/login", methods=["POST"])
@ratelimit_auth()
def login():
    """
    Authenticate and receive JWT tokens.
    ---
    tags:
      - Authentication
    operationId: loginUserV2
    summary: Log in and receive JWT access and refresh tokens
    description: >
      Validates credentials and returns a short-lived access token (24 h) and
      a long-lived refresh token (30 days).  Accounts are temporarily locked
      after 5 consecutive failed attempts from the same email.

      **Rate limit**: 5 requests / minute per IP.
    responses:
      200:
        description: Login successful — tokens returned.
      400:
        description: Email or password missing.
      401:
        description: Invalid credentials or account deactivated.
      423:
        description: Account temporarily locked.
      429:
        description: Rate limit exceeded.
      500:
        description: Internal server error.
    """
    try:
        data = request.get_json()

        if not data.get("email") or not data.get("password"):
            return jsonify({"error": "Email and password are required"}), 400

        email = data["email"].lower().strip()
        password = data["password"]

        if is_account_locked(email):
            return jsonify({
                "error": "Account temporarily locked due to multiple failed login attempts"
            }), 423

        user = User.query.filter_by(email=email).first()

        if not user or not user.check_password(password):
            log_login_attempt(
                email=email,
                ip_address=request.remote_addr,
                user_agent=request.headers.get("User-Agent", ""),
                success=False,
            )
            return jsonify({"error": "Invalid credentials"}), 401

        if not user.is_active:
            return jsonify({"error": "Account is deactivated"}), 401

        user.last_login = datetime.now(timezone.utc)
        db.session.commit()

        tokens = jwt_manager.generate_tokens(user)

        log_login_attempt(
            email=email,
            ip_address=request.remote_addr,
            user_agent=request.headers.get("User-Agent", ""),
            success=True,
        )

        return jsonify({
            "message": "Login successful",
            "user": user.to_dict(),
            **tokens,
        }), 200

    except Exception as exc:
        current_app.logger.error("Login error: %s\n%s", exc, traceback.format_exc())
        return jsonify({"error": "Login failed"}), 500


@auth_v2_bp.route("/refresh", methods=["POST"])
@ratelimit_auth()
def refresh():
    """
    Exchange a refresh token for a new access token.
    ---
    tags:
      - Authentication
    operationId: refreshTokenV2
    summary: Refresh an expired access token
    responses:
      200:
        description: New access token issued.
      400:
        description: Refresh token missing.
      401:
        description: Refresh token invalid or expired.
      500:
        description: Internal server error.
    """
    try:
        data = request.get_json()
        refresh_token = data.get("refresh_token")

        if not refresh_token:
            return jsonify({"error": "Refresh token is required"}), 400

        result = jwt_manager.refresh_access_token(refresh_token)

        if "error" in result:
            return jsonify(result), 401

        return jsonify(result), 200

    except Exception as exc:
        current_app.logger.error("Token refresh error: %s\n%s", exc, traceback.format_exc())
        return jsonify({"error": "Token refresh failed"}), 500


# ---------------------------------------------------------------------------
# Protected endpoints
# ---------------------------------------------------------------------------

@auth_v2_bp.route("/profile", methods=["GET"])
@token_required
def get_profile():
    """
    Retrieve the authenticated user's profile.
    ---
    tags:
      - Authentication
    operationId: getUserProfileV2
    summary: Get current user profile
    security:
      - BearerAuth: []
    responses:
      200:
        description: Profile retrieved.
      401:
        description: Missing or invalid JWT token.
      500:
        description: Internal server error.
    """
    try:
        return jsonify({"user": request.current_user.to_dict()}), 200
    except Exception as exc:
        current_app.logger.error("Profile error: %s", exc)
        return jsonify({"error": "Failed to get profile"}), 500


@auth_v2_bp.route("/profile", methods=["PUT"])
@token_required
def update_profile():
    """Update the authenticated user's profile (first/last name, organization)."""
    try:
        data = request.get_json()
        user = request.current_user

        for field in ("first_name", "last_name", "organization"):
            if field in data:
                setattr(user, field, data[field].strip() if data[field] else None)

        user.updated_at = datetime.now(timezone.utc)
        db.session.commit()

        return jsonify({
            "message": "Profile updated successfully",
            "user": user.to_dict(),
        }), 200

    except Exception as exc:
        db.session.rollback()
        current_app.logger.error("Profile update error: %s", exc)
        return jsonify({"error": "Profile update failed"}), 500


@auth_v2_bp.route("/change-password", methods=["POST"])
@token_required
@ratelimit_auth()
def change_password():
    """Change the authenticated user's password."""
    try:
        data = request.get_json()
        user = request.current_user

        current_password = data.get("current_password")
        new_password = data.get("new_password")

        if not current_password or not new_password:
            return jsonify({"error": "Current and new passwords are required"}), 400

        if not user.check_password(current_password):
            return jsonify({"error": "Current password is incorrect"}), 401

        password_validation = validate_password(new_password)
        if not password_validation["valid"]:
            return jsonify({"error": password_validation["message"]}), 400

        user.set_password(new_password)
        user.updated_at = datetime.now(timezone.utc)
        db.session.commit()

        return jsonify({"message": "Password changed successfully"}), 200

    except Exception as exc:
        db.session.rollback()
        current_app.logger.error("Password change error: %s", exc)
        return jsonify({"error": "Password change failed"}), 500


# ---------------------------------------------------------------------------
# Stub endpoints (not yet implemented)
# ---------------------------------------------------------------------------

@auth_v2_bp.route("/api-keys", methods=["GET", "POST"])
@auth_v2_bp.route("/api-keys/<key_id>", methods=["DELETE"])
@token_required
def api_keys_stub(key_id=None):
    """API key management via the auth namespace (stub — use /api/v3/developer/keys)."""
    return jsonify({"error": "Use /api/v3/developer/keys for API key management"}), 503


@auth_v2_bp.route("/forgot-password", methods=["POST"])
@ratelimit_auth()
def forgot_password():
    """Request a password reset email (not yet implemented — needs email service)."""
    return jsonify({"error": "Password reset functionality is not yet available"}), 503


@auth_v2_bp.route("/reset-password", methods=["POST"])
@ratelimit_auth()
def reset_password():
    """Reset password using a reset token (not yet implemented)."""
    return jsonify({"error": "Password reset functionality is not yet available"}), 503


# ---------------------------------------------------------------------------
# Admin endpoints
# ---------------------------------------------------------------------------

@auth_v2_bp.route("/admin/users", methods=["GET"])
@token_required
@admin_required
def get_users():
    """List all users (admin only), paginated."""
    try:
        page = request.args.get("page", 1, type=int)
        per_page = min(request.args.get("per_page", 20, type=int), 100)

        users = User.query.order_by(User.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )

        return jsonify({
            "users": [user.to_dict() for user in users.items],
            "pagination": {
                "page": page,
                "per_page": per_page,
                "total": users.total,
                "pages": users.pages,
                "has_next": users.has_next,
                "has_prev": users.has_prev,
            },
        }), 200

    except Exception as exc:
        current_app.logger.error("Get users error: %s", exc)
        return jsonify({"error": "Failed to get users"}), 500


@auth_v2_bp.route("/admin/users/<user_id>/deactivate", methods=["POST"])
@token_required
@admin_required
def deactivate_user(user_id):
    """Deactivate a user account (admin only)."""
    try:
        user = User.query.get(user_id)
        if not user:
            return jsonify({"error": "User not found"}), 404

        user.is_active = False
        user.updated_at = datetime.now(timezone.utc)
        db.session.commit()

        return jsonify({"message": "User deactivated successfully"}), 200

    except Exception as exc:
        db.session.rollback()
        current_app.logger.error("User deactivation error: %s", exc)
        return jsonify({"error": "User deactivation failed"}), 500


@auth_v2_bp.route("/admin/users/<user_id>/activate", methods=["POST"])
@token_required
@admin_required
def activate_user(user_id):
    """Activate a previously deactivated user account (admin only)."""
    try:
        user = User.query.get(user_id)
        if not user:
            return jsonify({"error": "User not found"}), 404

        user.is_active = True
        user.updated_at = datetime.now(timezone.utc)
        db.session.commit()

        return jsonify({"message": "User activated successfully"}), 200

    except Exception as exc:
        db.session.rollback()
        current_app.logger.error("User activation error: %s", exc)
        return jsonify({"error": "User activation failed"}), 500
