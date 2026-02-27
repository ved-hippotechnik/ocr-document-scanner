"""
api/auth/jwt_utils.py
=====================
Re-export of ``app.auth.jwt_utils`` for use within the ``api/`` package.

Importing from this module is equivalent to importing from the canonical
``app.auth.jwt_utils``.  It exists so that code inside ``app/api/`` can
reference a sibling-package path consistently:

    from app.api.auth.jwt_utils import token_required, ...

instead of crossing the package boundary:

    from app.auth.jwt_utils import token_required, ...

Both import paths resolve to the same underlying objects.
"""
from app.auth.jwt_utils import (  # noqa: F401 — re-export everything
    JWTManager,
    jwt_manager,
    token_required,
    api_key_required,
    token_or_api_key_required,
    scope_required,
    admin_required,
    role_required,
    check_rate_limit,
    log_login_attempt,
    get_current_user,
    is_account_locked,
)

__all__ = [
    "JWTManager",
    "jwt_manager",
    "token_required",
    "api_key_required",
    "token_or_api_key_required",
    "scope_required",
    "admin_required",
    "role_required",
    "check_rate_limit",
    "log_login_attempt",
    "get_current_user",
    "is_account_locked",
]
