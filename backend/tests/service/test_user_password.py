# SPDX-FileCopyrightText: Copyright © 2026 Mohd Izhar Firdaus Bin Ismail
# SPDX-License-Identifier: AGPLv3+

import pytest
import time
import jwt
from fastapi.testclient import TestClient
from mindweaver.config import settings
from mindweaver.fw.auth import User

def generate_token(user_id: int, email: str) -> str:
    payload = {
        "sub": email,
        "user_id": user_id,
        "exp": time.time() + 3600
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm="HS256")

def test_change_password_permissions(client: TestClient):
    original_enable_auth = settings.enable_auth
    
    try:
        # 1. Disable auth temporarily to create test users via API
        settings.enable_auth = False
        
        resp = client.post(
            "/api/v1/users",
            json={
                "name": "admin-pwd-test",
                "title": "Admin",
                "email": "admin@test.local",
                "password": "adminpassword123",
                "is_superadmin": True,
                "is_active": True
            }
        )
        assert resp.status_code == 200, resp.text
        admin_data = resp.json()["data"]

        resp = client.post(
            "/api/v1/users",
            json={
                "name": "user1-pwd-test",
                "title": "User 1",
                "email": "user1@test.local",
                "password": "user1password123",
                "is_superadmin": False,
                "is_active": True
            }
        )
        assert resp.status_code == 200, resp.text
        user1_data = resp.json()["data"]

        resp = client.post(
            "/api/v1/users",
            json={
                "name": "user2-pwd-test",
                "title": "User 2",
                "email": "user2@test.local",
                "password": "user2password123",
                "is_superadmin": False,
                "is_active": True
            }
        )
        assert resp.status_code == 200, resp.text
        user2_data = resp.json()["data"]

        # 2. Enable auth for the verification phase
        settings.enable_auth = True
        
        admin_token = generate_token(admin_data["id"], admin_data["email"])
        user1_token = generate_token(user1_data["id"], user1_data["email"])

        # Superadmin can change other user's password
        resp = client.post(
            f"/api/v1/users/{user1_data['id']}/_change_password",
            json={"password": "newadminchanged123"},
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert resp.status_code == 200, resp.text
        assert resp.json()["status"] == "success"

        # Regular user can change their own password
        resp = client.post(
            f"/api/v1/users/{user1_data['id']}/_change_password",
            json={"password": "newownchanged123"},
            headers={"Authorization": f"Bearer {user1_token}"}
        )
        assert resp.status_code == 200, resp.text

        # Regular user cannot change another user's password
        resp = client.post(
            f"/api/v1/users/{user2_data['id']}/_change_password",
            json={"password": "hackedpassword123"},
            headers={"Authorization": f"Bearer {user1_token}"}
        )
        assert resp.status_code == 403

        # Password validation constraint (minimum length 8)
        resp = client.post(
            f"/api/v1/users/{user1_data['id']}/_change_password",
            json={"password": "short"},
            headers={"Authorization": f"Bearer {user1_token}"}
        )
        assert resp.status_code == 422

    finally:
        settings.enable_auth = original_enable_auth
