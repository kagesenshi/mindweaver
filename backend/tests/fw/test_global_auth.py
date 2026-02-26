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
    """Save and restore auth-related settings around each test."""
    old_enable_auth = settings.enable_auth
    old_oidc_issuer = settings.oidc_issuer
    old_oidc_client_id = settings.oidc_client_id
    old_oidc_client_secret = settings.oidc_client_secret
    old_jwt_secret = settings.jwt_secret
    old_admin_user = settings.default_admin_username
    old_admin_pass = settings.default_admin_password
    settings.jwt_secret = "a_very_long_secret_key_for_testing_purposes_only_32_bytes"
    settings.default_admin_username = "admin"
    settings.default_admin_password = "password123"
    yield
    settings.enable_auth = old_enable_auth
    settings.oidc_issuer = old_oidc_issuer
    settings.oidc_client_id = old_oidc_client_id
    settings.oidc_client_secret = old_oidc_client_secret
    settings.jwt_secret = old_jwt_secret
    settings.default_admin_username = old_admin_user
    settings.default_admin_password = old_admin_pass


def _get_superadmin_headers(c: TestClient) -> dict:
    """Login as admin superuser and return authorization headers."""
    login_resp = c.post(
        "/api/v1/auth/login",
        json={"username": "admin", "password": "password123"},
    )
    assert login_resp.status_code == 200
    token = login_resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_health_accessible_without_auth(client: TestClient):
    """Health endpoint should be accessible even if auth is enabled."""
    settings.enable_auth = True
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_protected_endpoint_returns_401_no_token(client: TestClient):
    """Protected endpoints should return 401 when no token is provided."""
    settings.enable_auth = True
    response = client.get("/api/v1/projects")
    assert response.status_code == 401
    assert "Not authenticated" in response.text


def test_protected_endpoint_accessible_with_token(client: TestClient):
    """Protected endpoints should return 401 for a valid token but non-existent user."""
    settings.enable_auth = True
    token_payload = {"sub": "test@example.com", "user_id": 1, "exp": time.time() + 3600}
    token = jwt.encode(token_payload, settings.jwt_secret, algorithm="HS256")

    # Create a project (auth disabled by conftest default)
    client.post("/api/v1/projects", json={"name": "p1", "title": "P1"})

    # Now enable auth and try with token for non-existent user
    settings.enable_auth = True
    headers = {"Authorization": f"Bearer {token}"}
    response = client.get("/api/v1/projects", headers=headers)
    assert response.status_code == 401
    assert "User not found" in response.text


def test_auth_endpoints_exempt(client: TestClient):
    """Auth login and callback endpoints should be accessible without a token."""
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
    """OIDC callback should create a new user if one doesn't exist."""
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
    """OIDC callback should handle username conflicts by appending a suffix."""
    # Use lifespan to create the admin superuser, then login to create a conflicting user
    with client as c:
        settings.enable_auth = True
        admin_headers = _get_superadmin_headers(c)

        # Pre-create a user that will conflict, authenticated as superadmin
        response = c.post(
            "/api/v1/users",
            json={
                "name": "conflicted",
                "title": "Existing User",
                "email": "existing@example.com",
                "password": "password123",
            },
            headers=admin_headers,
        )
        assert response.status_code == 200

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
            response = c.post(
                "/api/v1/auth/callback",
                params={"code": "abc", "redirect_url": "http://localhost/callback"},
            )
            assert response.status_code == 200
            data = response.json()

        # Verify user was created with a suffixed name
        response = c.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {data['access_token']}"},
        )
        assert response.status_code == 200
        res_data = response.json()
        assert res_data["email"] == "newuser@example.com"
        assert res_data["name"].startswith("conflicted#")


def test_feature_flags_exempt(client: TestClient):
    """Feature flags endpoint should be accessible even if auth is enabled."""
    settings.enable_auth = True
    response = client.get("/feature-flags")
    assert response.status_code == 200
