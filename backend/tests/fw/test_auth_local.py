# SPDX-FileCopyrightText: Copyright © 2026 Mohd Izhar Firdaus Bin Ismail
# SPDX-License-Identifier: AGPLv3+

import pytest
from fastapi.testclient import TestClient
from mindweaver.config import settings
from mindweaver.fw.auth import get_password_hash


@pytest.fixture(autouse=True)
def setup_settings():
    """Configure admin credentials and enable auth for all tests."""
    old_admin_user = settings.default_admin_username
    old_admin_pass = settings.default_admin_password
    old_enable_auth = settings.enable_auth
    settings.default_admin_username = "admin"
    settings.default_admin_password = "password123"
    settings.enable_auth = True
    yield
    settings.default_admin_username = old_admin_user
    settings.default_admin_password = old_admin_pass
    settings.enable_auth = old_enable_auth


def _get_superadmin_headers(c: TestClient) -> dict:
    """Login as admin superuser and return authorization headers."""
    login_resp = c.post(
        "/api/v1/auth/login",
        json={"username": "admin", "password": "password123"},
    )
    assert login_resp.status_code == 200
    token = login_resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_local_login_success(client: TestClient):
    """Verify successful local login returns a bearer token."""
    with client as c:
        response = c.post(
            "/api/v1/auth/login",
            json={"username": "admin", "password": "password123"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"


def test_local_login_failure(client: TestClient):
    """Verify login with wrong password returns 401."""
    with client as c:
        response = c.post(
            "/api/v1/auth/login",
            json={"username": "admin", "password": "wrongpassword"},
        )
        assert response.status_code == 401
        assert "Invalid credentials" in response.json()["detail"]


def test_user_me_with_local_token(client: TestClient):
    """Verify /auth/me returns current user info with redacted password."""
    with client as c:
        headers = _get_superadmin_headers(c)

        response = c.get("/api/v1/auth/me", headers=headers)
        assert response.status_code == 200
        assert response.json()["name"] == "admin"
        # Ensure password is redacted (not in schema or filtered)
        assert response.json()["password"] == "__REDACTED__"


def test_feature_flags_oidc_disabled(client: TestClient):
    """Verify feature flags show oidc_enabled=False when no issuer is set."""
    old_issuer = settings.oidc_issuer
    settings.oidc_issuer = None
    try:
        response = client.get("/feature-flags")
        assert response.status_code == 200
        assert response.json()["oidc_enabled"] is False
    finally:
        settings.oidc_issuer = old_issuer


def test_feature_flags_oidc_enabled(client: TestClient):
    """Verify feature flags show oidc_enabled=True when issuer is set."""
    old_issuer = settings.oidc_issuer
    settings.oidc_issuer = "http://mock-issuer"
    try:
        response = client.get("/feature-flags")
        assert response.status_code == 200
        assert response.json()["oidc_enabled"] is True
    finally:
        settings.oidc_issuer = old_issuer


def test_user_management_crud(client: TestClient):
    """Verify full CRUD lifecycle for user management as superadmin."""
    with client as c:
        headers = _get_superadmin_headers(c)

        # Create user
        response = c.post(
            "/api/v1/users",
            json={
                "name": "newuser",
                "title": "New User",
                "email": "newuser@example.com",
                "password": "password123",
                "display_name": "New User",
            },
            headers=headers,
        )
        assert response.status_code == 200
        user_data = response.json()["data"]
        user_id = user_data["id"]
        assert user_data["password"] == "__REDACTED__"

        # List users
        response = c.get("/api/v1/users", headers=headers)
        assert response.status_code == 200
        users = response.json()["data"]
        assert any(u["name"] == "newuser" for u in users)
        for u in users:
            assert u["password"] == "__REDACTED__"

        # Update user
        response = c.put(
            f"/api/v1/users/{user_id}",
            json={"display_name": "Updated User"},
            headers=headers,
        )
        assert response.status_code == 200
        assert response.json()["data"]["password"] == "__REDACTED__"

        # Get individual user
        response = c.get(f"/api/v1/users/{user_id}", headers=headers)
        assert response.status_code == 200
        assert response.json()["data"]["password"] == "__REDACTED__"

        # Delete user
        headers.update({"X-RESOURCE-NAME": "newuser"})
        response = c.delete(f"/api/v1/users/{user_id}", headers=headers)
        assert response.status_code == 200


def test_non_superadmin_cannot_manage_users(client: TestClient):
    """Non-superadmin users should get 403 when trying to manage users."""
    with client as c:
        admin_headers = _get_superadmin_headers(c)

        # Create a regular (non-superadmin) user
        response = c.post(
            "/api/v1/users",
            json={
                "name": "regularuser",
                "title": "Regular User",
                "email": "regular@example.com",
                "password": "password123",
                "display_name": "Regular User",
            },
            headers=admin_headers,
        )
        assert response.status_code == 200

        # Login as regular user
        login_resp = c.post(
            "/api/v1/auth/login",
            json={"username": "regularuser", "password": "password123"},
        )
        assert login_resp.status_code == 200
        regular_token = login_resp.json()["access_token"]
        regular_headers = {"Authorization": f"Bearer {regular_token}"}

        # Regular user should NOT be able to create users
        response = c.post(
            "/api/v1/users",
            json={
                "name": "anotheruser",
                "title": "Another User",
                "email": "another@example.com",
                "password": "password123",
            },
            headers=regular_headers,
        )
        assert response.status_code == 403
