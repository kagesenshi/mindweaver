# SPDX-FileCopyrightText: Copyright © 2026 Mohd Izhar Firdaus Bin Ismail
# SPDX-License-Identifier: AGPLv3+

import asyncio
import logging
import time
from typing import Optional

from fastapi import HTTPException, Request
import httpx
import jwt
from sqlmodel import select

from mindweaver.config import settings
from mindweaver.fw.hash import get_password_hash, verify_password
from mindweaver.fw.model import AsyncSession

from .model import User

logger = logging.getLogger(__name__)

_oidc_config_cache: Optional[dict] = None
_oidc_last_fetched: float = 0
_oidc_fetch_lock = asyncio.Lock()


async def get_oidc_config(client: httpx.AsyncClient) -> dict:
    """Fetch or return cached OIDC discovery configuration."""
    global _oidc_config_cache, _oidc_last_fetched

    now = time.monotonic()
    # First check (unlocked)
    if _oidc_config_cache and (now - _oidc_last_fetched < 3600):
        return _oidc_config_cache

    async with _oidc_fetch_lock:
        # Second check (locked)
        if _oidc_config_cache and (now - _oidc_last_fetched < 3600):
            return _oidc_config_cache

        issuer = settings.oidc_issuer.rstrip("/")
        discovery_url = f"{issuer}/.well-known/openid-configuration"
        resp = await client.get(discovery_url)
        resp.raise_for_status()
        _oidc_config_cache = resp.json()
        _oidc_last_fetched = time.monotonic()
        return _oidc_config_cache


async def get_current_user(request: Request, session: AsyncSession) -> User:
    """Retrieve the current authenticated user from session/token or fallback if auth disabled."""
    if not settings.enable_auth:
        # If auth is disabled, we try to return the first available user,
        # preferring the default admin if it exists.
        # This is mainly for testing purposes.
        statement = select(User)
        if settings.default_admin_username:
            statement = statement.where(User.name == settings.default_admin_username)
        result = await session.exec(statement)
        user = result.first()
        if not user:
            # Try any user
            result = await session.exec(select(User))
            user = result.first()

        if user:
            return user

    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Not authenticated")

    token = auth_header.split(" ")[1]
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=["HS256"])
        user_email = payload.get("sub")
        if not user_email:
            raise HTTPException(status_code=401, detail="Invalid token")
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")

    statement = select(User).where(User.email == user_email)
    result = await session.exec(statement)
    user = result.first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user


async def get_superadmin(request: Request, session: AsyncSession) -> Optional[User]:
    """Verify that current user is a superadmin."""
    if not settings.enable_auth:
        return None

    user = await get_current_user(request, session)
    if user.is_superadmin:
        return user
    raise HTTPException(status_code=403, detail="Superadmin privileges required")


async def verify_token(
    request: Request,
    session: AsyncSession,
):
    """Verify bearer token for incoming requests unless exempt or auth is disabled."""
    if not settings.enable_auth:
        return

    # Exemptions
    path = request.url.path
    if path in ["/health", "/feature-flags", "/api/v1/_brand"]:
        return
    if "/api/v1/auth/login" in path or "/api/v1/auth/callback" in path:
        return

    user = await get_current_user(request, session)
    if hasattr(request, "state"):
        request.state.user = user


def redact_user(user: User) -> User:
    """Return a copy of user with password redacted."""
    if not user.password:
        return user
    user_dict = user.model_dump()
    user_dict["password"] = "__REDACTED__"
    return User.model_validate(user_dict)


class _AuthServiceMeta(type):
    """Metaclass for AuthService to lazy-load permissions attribute."""

    @property
    def permissions(cls):
        """Lazy-load permissions module."""
        from . import permission
        return permission


class AuthService(metaclass=_AuthServiceMeta):
    """Service providing authentication operations and permissions."""

    @classmethod
    def model_class(cls) -> type[User]:
        """Return User SQLModel class."""
        return User

    @classmethod
    def router(cls):
        """Return auth API router."""
        from .views import router
        return router
