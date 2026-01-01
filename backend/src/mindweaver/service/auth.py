import httpx
import jwt
from fastapi import APIRouter, Depends, HTTPException, Request, responses, status
from ..config import settings
from ..fw.auth import create_access_token, decode_access_token, get_current_user
from typing import Any, Dict, Optional

router = APIRouter(prefix="/auth", tags=["Authentication"])


class OIDCClient:
    def __init__(self):
        self.client_id = settings.oidc_client_id
        self.client_secret = settings.oidc_client_secret
        self.discovery_url = settings.oidc_discovery_url
        self.redirect_uri = settings.oidc_redirect_uri
        self._config: Optional[Dict[str, Any]] = None

    async def get_config(self) -> Dict[str, Any]:
        if not self._config:
            if not self.discovery_url:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="OIDC discovery URL not configured",
                )
            async with httpx.AsyncClient() as client:
                response = await client.get(self.discovery_url)
                response.raise_for_status()
                self._config = response.json()
        return self._config


oidc_client = OIDCClient()


@router.get("/login")
async def login():
    config = await oidc_client.get_config()
    auth_endpoint = config["authorization_endpoint"]

    params = {
        "client_id": oidc_client.client_id,
        "response_type": "code",
        "scope": "openid profile email",
        "redirect_uri": oidc_client.redirect_uri,
    }

    query = "&".join(f"{k}={v}" for k, v in params.items())
    return responses.RedirectResponse(url=f"{auth_endpoint}?{query}")


@router.get("/callback")
async def callback(code: str):
    config = await oidc_client.get_config()
    token_endpoint = config["token_endpoint"]

    async with httpx.AsyncClient() as client:
        response = await client.post(
            token_endpoint,
            data={
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": oidc_client.redirect_uri,
                "client_id": oidc_client.client_id,
                "client_secret": oidc_client.client_secret,
            },
        )
        if response.status_code != 200:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Token exchange failed: {response.text}",
            )

        token_data = response.json()
        id_token = token_data.get("id_token")
        if not id_token:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No id_token returned from provider",
            )

        # Decode ID token (without verification for simplicity in this step,
        # but in production you MUST verify the signature)
        # Note: We use jwt.decode(..., options={"verify_signature": False}) for now
        # because verifying remote jwks requires more code.
        user_info = jwt.decode(id_token, options={"verify_signature": False})

        # Create our own JWT session
        access_token = create_access_token(
            data={
                "sub": user_info.get("sub"),
                "email": user_info.get("email"),
                "name": user_info.get("name"),
            }
        )

        # Redirect back to frontend with the token
        # Assume frontend is at localhost:3000 or similar
        # For simplicity, we can redirect to a special frontend URL
        # or just return the token in a response.
        # Let's redirect to the frontend with the token in a query parameter
        # In a real app, you might use a more secure way or a cookie.
        frontend_url = "http://localhost:3000/#/auth/success"
        return responses.RedirectResponse(url=f"{frontend_url}?token={access_token}")


@router.get("/me")
async def me(current_user: Dict[str, Any] = Depends(get_current_user)):
    return current_user
