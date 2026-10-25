# SPDX-FileCopyrightText: Copyright © 2026 Mohd Izhar Firdaus Bin Ismail
# SPDX-License-Identifier: AGPLv3+

import random
import time
from urllib.parse import urlencode

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse
import httpx
import jwt
from sqlmodel import select

from mindweaver.config import settings
from mindweaver.fw.model import AsyncSession
from mindweaver.fw.permission import require

from .model import LoginRequest, Token, User, UserProfileUpdate
from .permission import Me, UpdateMe
from .service import (
    get_current_user,
    get_oidc_config,
    redact_user,
    verify_password,
)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=Token)
async def login(credentials: LoginRequest, session: AsyncSession):
    """Authenticate user with username and password."""
    statement = select(User).where(User.name == credentials.username)
    result = await session.exec(statement)
    user = result.first()
    if not user or not user.password:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    if not verify_password(credentials.password, user.password):
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

    scope = "openid profile email"
    state = "random_state"

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
    Frontend sends code and the original redirect_url.
    """
    if (
        not settings.oidc_issuer
        or not settings.oidc_client_id
        or not settings.oidc_client_secret
    ):
        raise HTTPException(status_code=500, detail="OIDC not configured")

    async with httpx.AsyncClient() as client:
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

        try:
            payload = jwt.decode(id_token, options={"verify_signature": False})
        except Exception:
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
            base_name = payload.get("preferred_username") or email.split("@")[0]
            user_name = base_name

            while True:
                statement = select(User).where(User.name == user_name)
                result = await session.exec(statement)
                if not result.first():
                    break
                user_name = f"{base_name}#{random.randint(1000, 9999)}"

            user = User(
                name=user_name,
                title=user_display_name,
                email=email,
                display_name=user_display_name,
            )
            session.add(user)
            await session.commit()
            await session.refresh(user)
        else:
            changed = False
            if payload.get("name") and user.display_name != payload.get("name"):
                user.display_name = payload.get("name")
                changed = True
            if changed:
                session.add(user)
                await session.commit()
                await session.refresh(user)

        app_token_payload = {
            "sub": user.email,
            "user_id": user.id,
            "exp": time.time() + 24 * 3600,  # 1 day
        }
        app_token = jwt.encode(
            app_token_payload, settings.jwt_secret, algorithm="HS256"
        )

        return Token(access_token=app_token, token_type="bearer")


@router.get("/me", response_model=User, dependencies=[require(Me)])
async def me(
    request: Request,
    session: AsyncSession,
    user: User = Depends(get_current_user),
):
    """Retrieve current authenticated user profile."""
    return redact_user(user)


@router.put("/me", response_model=User, dependencies=[require(UpdateMe)])
async def update_me(
    data: UserProfileUpdate,
    request: Request,
    session: AsyncSession,
    user: User = Depends(get_current_user),
):
    """Update current authenticated user profile."""
    if data.display_name is not None:
        user.display_name = data.display_name
    if data.title is not None:
        user.title = data.title

    session.add(user)
    await session.commit()
    await session.refresh(user)

    return redact_user(user)
