import pytest
from mindweaver.fw.auth import create_access_token, decode_access_token
from datetime import timedelta


def test_jwt_flow():
    data = {"sub": "user123", "email": "test@example.com"}
    token = create_access_token(data)
    assert token is not None

    payload = decode_access_token(token)
    assert payload["sub"] == "user123"
    assert payload["email"] == "test@example.com"
    assert "exp" in payload


def test_jwt_expiration():
    from fastapi import HTTPException

    data = {"sub": "user123"}
    # Create a token that expires in the past
    token = create_access_token(data, expires_delta=timedelta(seconds=-1))

    with pytest.raises(HTTPException) as excinfo:
        decode_access_token(token)
    assert excinfo.value.status_code == 401
    assert excinfo.value.detail == "Token has expired"


@pytest.mark.asyncio
async def test_auth_me_endpoint(client):
    data = {"sub": "user123", "email": "test@example.com"}
    token = create_access_token(data)

    response = client.get(
        "/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    assert response.json()["sub"] == "user123"
    assert response.json()["email"] == "test@example.com"


@pytest.mark.asyncio
async def test_auth_me_unauthorized(client):
    response = client.get("/api/v1/auth/me")
    assert response.status_code == 403  # HTTPBearer returns 403 if no header
