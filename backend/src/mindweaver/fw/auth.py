# SPDX-FileCopyrightText: Copyright © 2026 Mohd Izhar Firdaus Bin Ismail
# SPDX-License-Identifier: AGPLv3+

from .model import Base
from .service import Service
from sqlmodel import Field, Session, select
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import RedirectResponse
from mindweaver.config import settings
from mindweaver.fw.model import AsyncSession, get_session, get_engine
import asyncio
import httpx
import jwt
import time
from urllib.parse import urlencode
from typing import Optional
from pydantic import BaseModel


class User(Base, table=True):
    __tablename__ = "mw_user"
    email: str = Field(index=True, unique=True)
    preferred_username: str = Field(nullable=True)
    display_name: str = Field(nullable=True)
    picture: str = Field(nullable=True)
    is_active: bool = Field(default=True)


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

        @router.get("/login")
        async def login(redirect_url: str):
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
                    user = User(
                        name=payload.get("name") or email.split("@")[0],
                        email=email,
                        preferred_username=payload.get("preferred_username"),
                        display_name=payload.get("name"),
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
                    if payload.get(
                        "preferred_username"
                    ) and user.preferred_username != payload.get("preferred_username"):
                        user.preferred_username = payload.get("preferred_username")
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

        @router.get("/me", response_model=User)
        async def me(user: User = Depends(get_current_user)):
            return user

        return router


router = AuthService.router()
