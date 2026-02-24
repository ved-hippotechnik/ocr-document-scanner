"""
Authentication and authorization module
"""
from .jwt_utils import jwt_manager, token_required, api_key_required, token_or_api_key_required, admin_required, role_required, scope_required
from .routes import auth_bp

__all__ = [
    'jwt_manager',
    'token_required',
    'api_key_required',
    'token_or_api_key_required',
    'admin_required',
    'role_required',
    'scope_required',
    'auth_bp'
]