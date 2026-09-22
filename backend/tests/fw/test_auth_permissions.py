# SPDX-FileCopyrightText: Copyright © 2026 Mohd Izhar Firdaus Bin Ismail
# SPDX-License-Identifier: AGPLv3+

import pytest
from fastapi.testclient import TestClient
from mindweaver.config import settings


@pytest.fixture(autouse=True)
def setup_settings():
    """Save and restore auth-related settings around each test."""
    old_admin_user = settings.default_admin_username
    old_admin_pass = settings.default_admin_password
    old_enable_auth = settings.enable_auth
    settings.default_admin_username = "admin"
    settings.default_admin_password = "password123"
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


def _create_and_login_regular_user(c: TestClient, admin_headers: dict) -> tuple[dict, int]:
    """Create a regular (non-superadmin) user and return their auth headers and user id."""
    user_resp = c.post(
        "/api/v1/users",
        json={
            "name": "regularguy",
            "title": "Data Analyst",
            "email": "regularguy@example.com",
            "password": "password123",
            "display_name": "Regular Guy",
            "is_superadmin": False,
        },
        headers=admin_headers,
    )
    assert user_resp.status_code == 200
    user_id = user_resp.json()["data"]["id"]

    login_resp = c.post(
        "/api/v1/auth/login",
        json={"username": "regularguy", "password": "password123"},
    )
    assert login_resp.status_code == 200
    token = login_resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}, user_id


def _create_test_cluster(c: TestClient, admin_headers: dict) -> int:
    """Create a k8s cluster as admin and return its ID."""
    cluster_resp = c.post(
        "/api/v1/k8s_clusters",
        json={
            "name": f"perm-cluster-{id(c)}",
            "title": "Perm Cluster",
            "type": "remote",
            "kubeconfig": "dummy config",
        },
        headers=admin_headers,
    )
    assert cluster_resp.status_code == 200, cluster_resp.json()
    return cluster_resp.json()["data"]["id"]


def test_non_admin_read_access_allowed(client: TestClient):
    """Verify non-admin user can read / list resources."""
    settings.enable_auth = True
    with client as c:
        admin_headers = _get_superadmin_headers(c)
        reg_headers, _ = _create_and_login_regular_user(c, admin_headers)
        cluster_id = _create_test_cluster(c, admin_headers)

        # Superadmin creates a project
        p_resp = c.post(
            "/api/v1/projects",
            json={"name": "test-read-proj", "title": "Test Read", "k8s_cluster_id": cluster_id},
            headers=admin_headers,
        )
        assert p_resp.status_code == 200
        proj_id = p_resp.json()["data"]["id"]

        # Regular user can list projects
        resp = c.get("/api/v1/projects", headers=reg_headers)
        assert resp.status_code == 200
        projects = resp.json()["data"]
        assert any(p["id"] == proj_id for p in projects)

        # Regular user can get single project
        resp = c.get(f"/api/v1/projects/{proj_id}", headers=reg_headers)
        assert resp.status_code == 200
        assert resp.json()["data"]["name"] == "test-read-proj"


def test_non_admin_create_denied(client: TestClient):
    """Verify non-admin user cannot create objects."""
    settings.enable_auth = True
    with client as c:
        admin_headers = _get_superadmin_headers(c)
        reg_headers, _ = _create_and_login_regular_user(c, admin_headers)
        cluster_id = _create_test_cluster(c, admin_headers)

        resp = c.post(
            "/api/v1/projects",
            json={"name": "forbidden-proj", "title": "Forbidden", "k8s_cluster_id": cluster_id},
            headers=reg_headers,
        )
        assert resp.status_code == 403
        assert "Permission denied for 'create'" in resp.text


def test_non_admin_update_denied(client: TestClient):
    """Verify non-admin user cannot update objects."""
    settings.enable_auth = True
    with client as c:
        admin_headers = _get_superadmin_headers(c)
        reg_headers, _ = _create_and_login_regular_user(c, admin_headers)
        cluster_id = _create_test_cluster(c, admin_headers)

        # Superadmin creates a project
        p_resp = c.post(
            "/api/v1/projects",
            json={"name": "update-proj", "title": "Original Title", "k8s_cluster_id": cluster_id},
            headers=admin_headers,
        )
        assert p_resp.status_code == 200
        proj_id = p_resp.json()["data"]["id"]

        # Non-admin attempts to update
        resp = c.put(
            f"/api/v1/projects/{proj_id}",
            json={"title": "Hacked Title"},
            headers=reg_headers,
        )
        assert resp.status_code == 403
        assert "Permission denied for 'update'" in resp.text


def test_non_admin_delete_denied(client: TestClient):
    """Verify non-admin user cannot delete objects."""
    settings.enable_auth = True
    with client as c:
        admin_headers = _get_superadmin_headers(c)
        reg_headers, _ = _create_and_login_regular_user(c, admin_headers)
        cluster_id = _create_test_cluster(c, admin_headers)

        # Superadmin creates a project
        p_resp = c.post(
            "/api/v1/projects",
            json={"name": "delete-proj", "title": "Delete Title", "k8s_cluster_id": cluster_id},
            headers=admin_headers,
        )
        assert p_resp.status_code == 200
        proj_id = p_resp.json()["data"]["id"]

        # Non-admin attempts to delete
        delete_headers = dict(reg_headers)
        delete_headers["X-RESOURCE-NAME"] = "delete-proj"
        resp = c.delete(
            f"/api/v1/projects/{proj_id}",
            headers=delete_headers,
        )
        assert resp.status_code == 403
        assert "Permission denied for 'delete'" in resp.text


def test_non_admin_execute_denied(client: TestClient):
    """Verify non-admin user cannot execute platform actions."""
    settings.enable_auth = True
    with client as c:
        admin_headers = _get_superadmin_headers(c)
        reg_headers, _ = _create_and_login_regular_user(c, admin_headers)
        cluster_id = _create_test_cluster(c, admin_headers)

        p_resp = c.post(
            "/api/v1/projects",
            json={"name": "exec-proj", "title": "Exec Title", "k8s_cluster_id": cluster_id},
            headers=admin_headers,
        )
        proj_id = p_resp.json()["data"]["id"]

        # Create pgsql platform as admin
        admin_proj_headers = dict(admin_headers)
        admin_proj_headers["X-Project-Id"] = str(proj_id)
        pg_resp = c.post(
            "/api/v1/platform/pgsql",
            json={"name": "pg-inst", "title": "PG Inst", "project_id": proj_id, "instances": 1},
            headers=admin_proj_headers,
        )
        assert pg_resp.status_code == 200, pg_resp.json()
        pg_id = pg_resp.json()["data"]["id"]

        # Non-admin attempts deploy action
        reg_proj_headers = dict(reg_headers)
        reg_proj_headers["X-Project-Id"] = str(proj_id)
        resp = c.post(
            f"/api/v1/platform/pgsql/{pg_id}/_deploy",
            headers=reg_proj_headers,
        )
        assert resp.status_code == 403
        assert "Permission denied for 'execute'" in resp.text


def test_non_admin_self_profile_update(client: TestClient):
    """Verify non-admin user can update their own profile."""
    settings.enable_auth = True
    with client as c:
        admin_headers = _get_superadmin_headers(c)
        reg_headers, user_id = _create_and_login_regular_user(c, admin_headers)

        # Call PUT /api/v1/auth/me
        resp = c.put(
            "/api/v1/auth/me",
            json={"display_name": "Cool Guy", "title": "Principal Architect"},
            headers=reg_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["display_name"] == "Cool Guy"
        assert data["title"] == "Principal Architect"
        assert data["is_superadmin"] is False
        assert data["password"] == "__REDACTED__"

        # Verify via GET /api/v1/auth/me
        get_resp = c.get("/api/v1/auth/me", headers=reg_headers)
        assert get_resp.status_code == 200
        assert get_resp.json()["display_name"] == "Cool Guy"
        assert get_resp.json()["title"] == "Principal Architect"


def test_non_admin_self_password_change(client: TestClient):
    """Verify non-admin user can change their own password."""
    settings.enable_auth = True
    with client as c:
        admin_headers = _get_superadmin_headers(c)
        reg_headers, user_id = _create_and_login_regular_user(c, admin_headers)

        # Change own password
        resp = c.post(
            f"/api/v1/users/{user_id}/_change_password",
            json={"password": "newpassword456"},
            headers=reg_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "success"

        # Verify login with new password
        login_resp = c.post(
            "/api/v1/auth/login",
            json={"username": "regularguy", "password": "newpassword456"},
        )
        assert login_resp.status_code == 200
        assert "access_token" in login_resp.json()


def test_non_admin_cannot_change_other_user_password(client: TestClient):
    """Verify non-admin user cannot change another user's password."""
    settings.enable_auth = True
    with client as c:
        admin_headers = _get_superadmin_headers(c)
        reg_headers, _ = _create_and_login_regular_user(c, admin_headers)

        # Admin user has id 1
        resp = c.post(
            "/api/v1/users/1/_change_password",
            json={"password": "hackedpassword"},
            headers=reg_headers,
        )
        assert resp.status_code == 403
        assert "Not authorized to change this user's password" in resp.text
