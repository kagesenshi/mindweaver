# SPDX-FileCopyrightText: Copyright © 2026 Mohd Izhar Firdaus Bin Ismail
# SPDX-License-Identifier: AGPLv3+

from .model import (
    User,
    Token,
    LoginRequest,
    UserProfileUpdate,
    ChangePasswordRequest,
)
from .service import (
    AuthService,
    get_oidc_config,
    get_current_user,
    get_superadmin,
    verify_token,
    redact_user,
    get_password_hash,
    verify_password,
)

__all__ = [
    "User",
    "Token",
    "LoginRequest",
    "UserProfileUpdate",
    "ChangePasswordRequest",
    "AuthService",
    "get_oidc_config",
    "get_current_user",
    "get_superadmin",
    "verify_token",
    "redact_user",
    "get_password_hash",
    "verify_password",
    "permission",
    "router",
]


def __getattr__(name: str):
    """Fallback to lazy-import modules and symbols to prevent circular dependencies."""
    if name == "permission":
        from . import permission
        return permission
    if name == "router":
        from .views import router
        return router
    if name == "user_router":
        from mindweaver.service.user import router
        return router
    if name == "UserService":
        from mindweaver.service.user import UserService
        return UserService
    if name == "ChangePasswordRequest":
        from mindweaver.service.user import ChangePasswordRequest
        return ChangePasswordRequest
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
