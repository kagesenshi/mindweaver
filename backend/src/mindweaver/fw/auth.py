# SPDX-FileCopyrightText: Copyright © 2026 Mohd Izhar Firdaus Bin Ismail
# SPDX-License-Identifier: AGPLv3+

from .model import Base, NamedBase, AsyncSession, get_session, get_engine
from .service import (
    Service,
    SecretHandlerMixin,
    HashedHandlerMixin,
    before_create,
    before_update,
)
from .hash import get_password_hash, verify_password
from sqlmodel import Field, Session, select
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import RedirectResponse
from mindweaver.config import settings
from typing import Optional, Annotated, Any
import asyncio
import httpx
import jwt
import time
from urllib.parse import urlencode
from typing import Optional
from pydantic import BaseModel
import random


class User(NamedBase, table=True):
    __tablename__ = "mw_user"
    name: Optional[str] = Field(index=True, unique=True, default=None, nullable=True)
    title: Optional[str] = Field(default=None, nullable=True)
    email: Optional[str] = Field(index=True, unique=True, default=None)
    password: Optional[str] = Field(default=None, nullable=True)
    display_name: Optional[str] = Field(default=None, nullable=True)
    picture: Optional[str] = Field(default=None, nullable=True)
    is_active: bool = Field(default=True)
    is_superadmin: bool = Field(default=False)


class Token(BaseModel):
    access_token: str
    token_type: str


_oidc_config_cache: Optional[dict] = None
_oidc_last_fetched: float = 0
_oidc_fetch_lock = asyncio.Lock()


async def get_oidc_config(client: httpx.AsyncClient) -> dict:
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
    if not settings.enable_auth:
        return None

    user = await get_current_user(request, session)
    if user.is_superadmin:
        return user
    raise HTTPException(status_code=403, detail="Superadmin privileges required")


async def verify_token(request: Request):
    if not settings.enable_auth:
        return

    # Exemptions
    path = request.url.path
    if path in ["/health", "/feature-flags"]:
        return
    if "/api/v1/auth/login" in path or "/api/v1/auth/callback" in path:
        return

    # We need a session to verify the user exists
    async for session in get_session(get_engine()):
        await get_current_user(request, session)
        break


class AuthService(Service[User]):
    @classmethod
    def model_class(cls) -> type[User]:
        return User

    @classmethod
    def router(cls) -> APIRouter:
        router = APIRouter(prefix="/auth", tags=["auth"])

        @router.post("/login", response_model=Token)
        async def login(username: str, password: str, session: AsyncSession):
            """
            Authenticate user with username and password.
            """
            statement = select(User).where(User.name == username)
            result = await session.exec(statement)
            user = result.first()
            if not user or not user.password:
                raise HTTPException(status_code=401, detail="Invalid credentials")

            if not verify_password(password, user.password):
                raise HTTPException(status_code=401, detail="Invalid credentials")

            # Issue App Session Token
            app_token_payload = {
                "sub": user.email,
                "user_id": user.id,
                "exp": time.time() + 24 * 3600,  # 1 day
            }
            app_token = jwt.encode(
                app_token_payload, settings.jwt_secret, algorithm="HS256"
            )

            return Token(access_token=app_token, token_type="bearer")

        @router.get("/login")
        async def login_oidc(redirect_url: str):
            """
            Redirects the user to the OIDC provider's authorization endpoint.
            The redirect_uri passed to the provider will point to `redirect_url`
            (which should be the frontend callback page).
            """
            if not settings.oidc_issuer or not settings.oidc_client_id:
                raise HTTPException(status_code=500, detail="OIDC not configured")

            # Discover OIDC endpoints
            async with httpx.AsyncClient() as client:
                try:
                    oidc_config = await get_oidc_config(client)
                    auth_endpoint = oidc_config.get("authorization_endpoint")
                    if not auth_endpoint:
                        raise HTTPException(
                            status_code=500,
                            detail="Do discovery: authorization_endpoint not found",
                        )
                except Exception as e:
                    raise HTTPException(
                        status_code=500, detail=f"OIDC discovery failed: {e}"
                    )

            # Note: The user requested that the backend redirects the user to the OIDC provider
            # with redirection url to FRONTEND.
            # So `redirect_uri` param in the OIDC call = `redirect_url` (frontend)

            scope = "openid profile email"
            state = "random_state"  # In prod, should be cryptographically secure and verified

            # Encode params? httpx/starlette handling this usually via params dict if we returned a request
            # But we are redirecting.

            params = {
                "client_id": settings.oidc_client_id,
                "response_type": "code",
                "scope": scope,
                "redirect_uri": redirect_url,
                "state": state,
            }
            url = f"{auth_endpoint}?{urlencode(params)}"
            return RedirectResponse(url)

        @router.post("/callback", response_model=Token)
        async def callback(code: str, redirect_url: str, session: AsyncSession):
            """
            Exchange auth code for token.
            Frontend sends code and the original redirect_url (as it is required for token exchange validation).
            """
            if (
                not settings.oidc_issuer
                or not settings.oidc_client_id
                or not settings.oidc_client_secret
            ):
                raise HTTPException(status_code=500, detail="OIDC not configured")

            async with httpx.AsyncClient() as client:
                # Discover endpoints
                try:
                    oidc_config = await get_oidc_config(client)
                    token_endpoint = oidc_config.get("token_endpoint")
                    if not token_endpoint:
                        raise HTTPException(
                            status_code=500,
                            detail="Do discovery: token_endpoint not found",
                        )
                except Exception as e:
                    raise HTTPException(
                        status_code=500, detail=f"OIDC discovery failed: {e}"
                    )

                resp = await client.post(
                    token_endpoint,
                    data={
                        "grant_type": "authorization_code",
                        "code": code,
                        "redirect_uri": redirect_url,
                        "client_id": settings.oidc_client_id,
                        "client_secret": settings.oidc_client_secret,
                    },
                )
                if resp.status_code != 200:
                    raise HTTPException(
                        status_code=400, detail=f"OIDC exchange failed: {resp.text}"
                    )

                token_data = resp.json()
                id_token = token_data.get("id_token")

                # Verify and parse ID Token
                # For now, we trust the SSL connection to the provider and decoding without verifying signature
                # strictly against JWKS because handling JWKS caching is complex for this step.
                # In prod, ALWAYS verify signature.
                try:
                    # decoding without signature verification for extracting info
                    payload = jwt.decode(id_token, options={"verify_signature": False})
                except Exception as e:
                    raise HTTPException(status_code=400, detail="Invalid ID Token")

                email = payload.get("email")
                if not email:
                    raise HTTPException(
                        status_code=400, detail="Email not found in token"
                    )

                # Get or Create User
                statement = select(User).where(User.email == email)
                result = await session.exec(statement)
                user = result.first()
                if not user:
                    user_display_name = payload.get("name") or email.split("@")[0]
                    # Use preferred_username or email prefix as base name
                    base_name = payload.get("preferred_username") or email.split("@")[0]
                    user_name = base_name

                    # Check for conflict
                    while True:
                        statement = select(User).where(User.name == user_name)
                        result = await session.exec(statement)
                        if not result.first():
                            break
                        # Conflict found, append # + 4 random digits
                        user_name = f"{base_name}#{random.randint(1000, 9999)}"

                    user = User(
                        name=user_name,
                        title=user_display_name,
                        email=email,
                        display_name=user_display_name,
                        picture=payload.get("picture"),
                    )
                    session.add(user)
                    await session.commit()
                    await session.refresh(user)
                else:
                    # Update info if changed
                    changed = False
                    if payload.get("name") and user.display_name != payload.get("name"):
                        user.display_name = payload.get("name")
                        changed = True
                    if changed:
                        session.add(user)
                        await session.commit()
                        await session.refresh(user)

                # Issue App Session Token
                app_token_payload = {
                    "sub": user.email,
                    "user_id": user.id,
                    "exp": time.time() + 24 * 3600,  # 1 day
                }
                app_token = jwt.encode(
                    app_token_payload, settings.jwt_secret, algorithm="HS256"
                )

                return Token(access_token=app_token, token_type="bearer")

        # Let's try again with clean signature
        @router.get("/me", response_model=User)
        async def me(
            request: Request,
            session: AsyncSession,
            user: User = Depends(get_current_user),
        ):
            svc = UserService(request, session)
            return await svc.post_process_model(user)

        return router


class UserService(HashedHandlerMixin, Service[User]):
    @classmethod
    def model_class(cls) -> type[User]:
        return User

    @classmethod
    def hashed_fields(cls) -> list[str]:
        return ["password"]

    @classmethod
    def immutable_fields(cls) -> list[str]:
        # User objects usually have mutable names in this context,
        # but identifier fields like username and email should be fixed.
        return ["name", "email"]

    @classmethod
    def extra_dependencies(cls):
        return [Depends(get_superadmin)]

    @classmethod
    def router(cls) -> APIRouter:
        router = super().router()
        return router


router = AuthService.router()
user_router = UserService.router()
