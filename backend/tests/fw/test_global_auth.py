# SPDX-FileCopyrightText: Copyright © 2026 Mohd Izhar Firdaus Bin Ismail
# SPDX-License-Identifier: AGPLv3+

import pytest
import jwt
import time
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from mindweaver.config import settings
from mindweaver.fw.auth import User


@pytest.fixture(autouse=True)
def manage_auth_setting():
    old_enable_auth = settings.enable_auth
    old_oidc_issuer = settings.oidc_issuer
    old_oidc_client_id = settings.oidc_client_id
    old_oidc_client_secret = settings.oidc_client_secret
    old_jwt_secret = settings.jwt_secret
    settings.jwt_secret = "a_very_long_secret_key_for_testing_purposes_only_32_bytes"
    yield
    settings.enable_auth = old_enable_auth
    settings.oidc_issuer = old_oidc_issuer
    settings.oidc_client_id = old_oidc_client_id
    settings.oidc_client_secret = old_oidc_client_secret
    settings.jwt_secret = old_jwt_secret


def test_health_accessible_without_auth(client: TestClient):
    # health should be accessible even if auth is enabled
    settings.enable_auth = True
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_protected_endpoint_returns_401_no_token(client: TestClient):
    settings.enable_auth = True
    response = client.get("/api/v1/projects")
    assert response.status_code == 401
    assert "Not authenticated" in response.text


def test_protected_endpoint_accessible_with_token(client: TestClient):
    settings.enable_auth = True
    token_payload = {"sub": "test@example.com", "user_id": 1, "exp": time.time() + 3600}
    token = jwt.encode(token_payload, settings.jwt_secret, algorithm="HS256")

    # Setup: disable auth to create the project/user for testing
    settings.enable_auth = False
    client.post("/api/v1/projects", json={"name": "p1", "title": "P1"})

    # Now enable auth and try with token
    settings.enable_auth = True
    headers = {"Authorization": f"Bearer {token}"}
    response = client.get("/api/v1/projects", headers=headers)
    assert response.status_code == 401
    assert "User not found" in response.text


def test_auth_endpoints_exempt(client: TestClient):
    settings.enable_auth = True
    settings.oidc_issuer = "http://mock-issuer"
    settings.oidc_client_id = "mock-client-id"
    settings.oidc_client_secret = "mock-client-secret"

    mock_discovery_resp = MagicMock()
    mock_discovery_resp.status_code = 200
    mock_discovery_resp.json.return_value = {
        "authorization_endpoint": "http://mock-issuer/auth",
        "token_endpoint": "http://mock-issuer/token",
    }

    with patch("httpx.AsyncClient.get", return_value=mock_discovery_resp):
        response = client.get(
            "/api/v1/auth/login",
            params={"redirect_url": "http://localhost/callback"},
            follow_redirects=False,
        )
        assert response.status_code == 307

    mock_token_resp = MagicMock()
    mock_token_resp.status_code = 200
    mock_id_token = jwt.encode(
        {"email": "test@example.com", "name": "Test User"},
        "a_very_long_secret_key_for_testing_purposes_only_32_bytes",
        algorithm="HS256",
    )
    mock_token_resp.json.return_value = {"id_token": mock_id_token}

    with patch("httpx.AsyncClient.get", return_value=mock_discovery_resp), patch(
        "httpx.AsyncClient.post", return_value=mock_token_resp
    ):
        response = client.post(
            "/api/v1/auth/callback",
            params={"code": "abc", "redirect_url": "http://localhost/callback"},
        )
        assert response.status_code != 401


def test_auth_callback_creates_user(client: TestClient):
    settings.enable_auth = True
    settings.oidc_issuer = "http://mock-issuer"
    settings.oidc_client_id = "mock-client-id"
    settings.oidc_client_secret = "mock-client-secret"

    mock_discovery_resp = MagicMock()
    mock_discovery_resp.status_code = 200
    mock_discovery_resp.json.return_value = {
        "authorization_endpoint": "http://mock-issuer/auth",
        "token_endpoint": "http://mock-issuer/token",
    }

    mock_token_resp = MagicMock()
    mock_token_resp.status_code = 200
    mock_id_token = jwt.encode(
        {"email": "newuser@example.com", "name": "New User"},
        "a_very_long_secret_key_for_testing_purposes_only_32_bytes",
        algorithm="HS256",
    )
    mock_token_resp.json.return_value = {"id_token": mock_id_token}

    with patch("httpx.AsyncClient.get", return_value=mock_discovery_resp), patch(
        "httpx.AsyncClient.post", return_value=mock_token_resp
    ):
        response = client.post(
            "/api/v1/auth/callback",
            params={"code": "abc", "redirect_url": "http://localhost/callback"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data

    # Verify user was created
    response = client.get(
        "/api/v1/auth/me", headers={"Authorization": f"Bearer {data['access_token']}"}
    )
    assert response.status_code == 200
    assert response.json()["email"] == "newuser@example.com"


def test_auth_callback_handles_username_conflict(client: TestClient):
    # Pre-create a user that will conflict
    settings.enable_auth = False
    # Now that settings.enable_auth = False is also checked by get_superadmin, this works
    client.post(
        "/api/v1/users",
        json={
            "name": "conflicted",
            "title": "Existing User",
            "email": "existing@example.com",
            "password": "password123",
        },
    )
    settings.enable_auth = True
    settings.oidc_issuer = "http://mock-issuer"
    settings.oidc_client_id = "mock-client-id"
    settings.oidc_client_secret = "mock-client-secret"

    mock_discovery_resp = MagicMock()
    mock_discovery_resp.status_code = 200
    mock_discovery_resp.json.return_value = {
        "authorization_endpoint": "http://mock-issuer/auth",
        "token_endpoint": "http://mock-issuer/token",
    }

    mock_token_resp = MagicMock()
    mock_token_resp.status_code = 200
    mock_id_token = jwt.encode(
        {
            "email": "newuser@example.com",
            "preferred_username": "conflicted",
            "name": "New User",
        },
        "a_very_long_secret_key_for_testing_purposes_only_32_bytes",
        algorithm="HS256",
    )
    mock_token_resp.json.return_value = {"id_token": mock_id_token}

    with patch("httpx.AsyncClient.get", return_value=mock_discovery_resp), patch(
        "httpx.AsyncClient.post", return_value=mock_token_resp
    ):
        response = client.post(
            "/api/v1/auth/callback",
            params={"code": "abc", "redirect_url": "http://localhost/callback"},
        )
        assert response.status_code == 200
        data = response.json()

    # Verify user was created with a suffixed name
    response = client.get(
        "/api/v1/auth/me", headers={"Authorization": f"Bearer {data['access_token']}"}
    )
    assert response.status_code == 200
    res_data = response.json()
    assert res_data["email"] == "newuser@example.com"
    assert res_data["name"].startswith("conflicted#")


def test_feature_flags_exempt(client: TestClient):
    settings.enable_auth = True
    response = client.get("/feature-flags")
    assert response.status_code == 200
