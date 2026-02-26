# SPDX-FileCopyrightText: Copyright © 2026 Mohd Izhar Firdaus Bin Ismail
# SPDX-License-Identifier: AGPLv3+

import pytest
from fastapi.testclient import TestClient
from mindweaver.config import settings
from mindweaver.fw.auth import get_password_hash


@pytest.fixture(autouse=True)
def setup_settings():
    old_admin_user = settings.default_admin_username
    old_admin_pass = settings.default_admin_password
    settings.default_admin_username = "admin"
    settings.default_admin_password = "password123"
    yield
    settings.default_admin_username = old_admin_user
    settings.default_admin_password = old_admin_pass


def test_local_login_success(client: TestClient):
    # Ensure user exists (startup logic creates it)
    with client as c:
        response = c.post(
            "/api/v1/auth/login",
            params={"username": "admin", "password": "password123"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"


def test_local_login_failure(client: TestClient):
    with client as c:
        response = c.post(
            "/api/v1/auth/login",
            params={"username": "admin", "password": "wrongpassword"},
        )
        assert response.status_code == 401
        assert "Invalid credentials" in response.json()["detail"]


def test_user_me_with_local_token(client: TestClient):
    with client as c:
        login_resp = c.post(
            "/api/v1/auth/login",
            params={"username": "admin", "password": "password123"},
        )
        token = login_resp.json()["access_token"]

        response = c.get(
            "/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        assert response.json()["name"] == "admin"
        # Ensure password is redacted (not in schema or filtered)
        assert response.json()["password"] == "__REDACTED__"


def test_feature_flags_oidc_disabled(client: TestClient):
    old_issuer = settings.oidc_issuer
    settings.oidc_issuer = None
    try:
        response = client.get("/feature-flags")
        assert response.status_code == 200
        assert response.json()["oidc_enabled"] is False
    finally:
        settings.oidc_issuer = old_issuer


def test_feature_flags_oidc_enabled(client: TestClient):
    old_issuer = settings.oidc_issuer
    settings.oidc_issuer = "http://mock-issuer"
    try:
        response = client.get("/feature-flags")
        assert response.status_code == 200
        assert response.json()["oidc_enabled"] is True
    finally:
        settings.oidc_issuer = old_issuer


def test_user_management_crud(client: TestClient):
    with client as c:
        # Login as admin
        login_resp = c.post(
            "/api/v1/auth/login",
            params={"username": "admin", "password": "password123"},
        )
        assert login_resp.status_code == 200
        token = login_resp.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

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
