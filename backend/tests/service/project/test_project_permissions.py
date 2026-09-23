# SPDX-FileCopyrightText: Copyright © 2026 Mohd Izhar Firdaus Bin Ismail
# SPDX-License-Identifier: AGPLv3+

import pytest
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient
from mindweaver.config import settings
from mindweaver.fw.permission import (
    All,
    Permission,
    Read as FwRead,
    Write as FwWrite,
    List as FwList,
    View as FwView,
    Create as FwCreate,
    Update as FwUpdate,
    Delete as FwDelete,
    Execute as FwExecute,
    check_user_permission,
    _NAME_TO_PERMISSION,
)
from mindweaver.service.project.permission import (
    Manage,
    ManageProject,
    Project,
    Read,
    List,
    View,
    Write,
    Create,
    Update,
    Delete,
    Execute,
    Refresh,
    DownloadCert,
    CertManager,
    IssuerCert,
    CertificateDetails,
    RenewCertificate,
    ManageProjectPermission,
    ProjectPermission,
    ProjectRead,
    ProjectList,
    ProjectView,
    ProjectWrite,
    ProjectCreate,
    ProjectUpdate,
    ProjectDelete,
    ProjectExecute,
    ProjectRefresh,
    ProjectDownloadCert,
    ProjectCertManager,
    ProjectIssuerCert,
    ProjectCertificateDetails,
    ProjectRenewCertificate,
)


class DummyUser:
    """Mock user class for permission testing."""

    def __init__(self, is_superadmin: bool = False, permissions: list | None = None):
        """Initialize mock user with superadmin status and permissions list."""
        self.is_superadmin = is_superadmin
        self.permissions = permissions


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


def _create_and_login_user(
    c: TestClient, admin_headers: dict, username: str, permissions: list | None = None
) -> dict:
    """Create a user with specified permissions and return auth headers."""
    user_resp = c.post(
        "/api/v1/users",
        json={
            "name": username,
            "title": "Engineer",
            "email": f"{username}@example.com",
            "password": "password123",
            "display_name": username.capitalize(),
            "is_superadmin": False,
        },
        headers=admin_headers,
    )
    assert user_resp.status_code == 200

    login_resp = c.post(
        "/api/v1/auth/login",
        json={"username": username, "password": "password123"},
    )
    assert login_resp.status_code == 200
    token = login_resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def _create_k8s_cluster(c: TestClient, headers: dict) -> int:
    """Helper to create a k8s cluster for project testing."""
    resp = c.post(
        "/api/v1/k8s_clusters",
        json={
            "name": "perm-k8s-cluster",
            "title": "Perm K8s Cluster",
            "cluster_type": "generic",
            "ingress_mode": "nodeport",
            "is_active": True,
        },
        headers=headers,
    )
    assert resp.status_code == 200, resp.text
    return resp.json()["data"]["id"]


def test_project_permission_hierarchy():
    """Verify Project permission classes inherit correctly from All, Permission, and fw classes."""
    assert issubclass(Manage, Permission)
    assert issubclass(Manage, All)

    # Read hierarchy (inherits from Manage and FwRead)
    assert issubclass(Read, Manage)
    assert issubclass(Read, FwRead)
    assert issubclass(List, Read)
    assert issubclass(List, Manage)
    assert issubclass(List, FwList)
    assert issubclass(View, Read)
    assert issubclass(View, Manage)
    assert issubclass(View, FwView)

    # Write hierarchy (inherits from Manage)
    assert issubclass(Write, Manage)
    assert not issubclass(Write, Read)
    assert issubclass(Write, FwWrite)
    assert issubclass(Create, Write)
    assert not issubclass(Create, Read)
    assert issubclass(Create, FwCreate)
    assert issubclass(Update, Write)
    assert not issubclass(Update, Read)
    assert issubclass(Update, FwUpdate)
    assert issubclass(Delete, Write)
    assert not issubclass(Delete, Read)
    assert issubclass(Delete, FwDelete)

    # Execute hierarchy (inherits from Manage)
    assert issubclass(Execute, Manage)
    assert not issubclass(Execute, Read)
    assert issubclass(Execute, FwExecute)
    assert issubclass(RenewCertificate, Execute)
    assert not issubclass(RenewCertificate, Read)

    # Custom view hierarchy (all inherit from View -> Read -> Manage)
    assert issubclass(Refresh, View)
    assert issubclass(Refresh, Read)
    assert issubclass(Refresh, Manage)
    assert issubclass(DownloadCert, View)
    assert issubclass(DownloadCert, Read)
    assert issubclass(DownloadCert, Manage)
    assert issubclass(CertManager, View)
    assert issubclass(CertManager, Read)
    assert issubclass(CertManager, Manage)
    assert issubclass(IssuerCert, View)
    assert issubclass(IssuerCert, Read)
    assert issubclass(IssuerCert, Manage)
    assert issubclass(CertificateDetails, View)
    assert issubclass(CertificateDetails, Read)
    assert issubclass(CertificateDetails, Manage)

    # Aliases
    assert ManageProject is Manage
    assert ManageProjectPermission is Manage
    assert Project is Manage
    assert ProjectPermission is Manage
    assert ProjectRead is Read
    assert ProjectList is List
    assert ProjectView is View
    assert ProjectWrite is Write
    assert ProjectCreate is Create
    assert ProjectUpdate is Update
    assert ProjectDelete is Delete
    assert ProjectExecute is Execute
    assert ProjectRefresh is Refresh
    assert ProjectDownloadCert is DownloadCert
    assert ProjectCertManager is CertManager
    assert ProjectIssuerCert is IssuerCert
    assert ProjectCertificateDetails is CertificateDetails
    assert ProjectRenewCertificate is RenewCertificate


def test_project_permission_string_registration():
    """Verify that Project permission names are registered in _NAME_TO_PERMISSION via init_subclass."""
    assert _NAME_TO_PERMISSION.get("project:manage") is Manage
    assert _NAME_TO_PERMISSION.get("project:read") is Read
    assert _NAME_TO_PERMISSION.get("project:list") is List
    assert _NAME_TO_PERMISSION.get("project:view") is View
    assert _NAME_TO_PERMISSION.get("project:write") is Write
    assert _NAME_TO_PERMISSION.get("project:create") is Create
    assert _NAME_TO_PERMISSION.get("project:update") is Update
    assert _NAME_TO_PERMISSION.get("project:delete") is Delete
    assert _NAME_TO_PERMISSION.get("project:execute") is Execute
    assert _NAME_TO_PERMISSION.get("project:refresh") is Refresh
    assert _NAME_TO_PERMISSION.get("project:download_cert") is DownloadCert
    assert _NAME_TO_PERMISSION.get("project:cert_manager") is CertManager
    assert _NAME_TO_PERMISSION.get("project:issuer_cert") is IssuerCert
    assert _NAME_TO_PERMISSION.get("project:certificate_details") is CertificateDetails
    assert _NAME_TO_PERMISSION.get("project:renew_certificate") is RenewCertificate
    # Verify removed view_project is not registered
    assert "project:view_project" not in _NAME_TO_PERMISSION
    assert "project" not in _NAME_TO_PERMISSION
    assert "manage_project" not in _NAME_TO_PERMISSION


def test_project_check_user_permission_rules():
    """Verify check_user_permission evaluates service permissions accurately."""
    # 1. Superadmin has everything
    superadmin = DummyUser(is_superadmin=True)
    assert check_user_permission(superadmin, Manage)
    assert check_user_permission(superadmin, Read)
    assert check_user_permission(superadmin, List)
    assert check_user_permission(superadmin, Create)
    assert check_user_permission(superadmin, Refresh)

    # 2. User with Manage permission has all project actions
    proj_admin = DummyUser(permissions=[Manage])
    assert check_user_permission(proj_admin, Manage)
    assert check_user_permission(proj_admin, Read)
    assert check_user_permission(proj_admin, List)
    assert check_user_permission(proj_admin, View)
    assert check_user_permission(proj_admin, Create)
    assert check_user_permission(proj_admin, Update)
    assert check_user_permission(proj_admin, Delete)
    assert check_user_permission(proj_admin, Refresh)
    assert check_user_permission(proj_admin, RenewCertificate)
    assert check_user_permission(proj_admin, CertificateDetails)
    assert check_user_permission(proj_admin, DownloadCert)

    # 3. User with ProjectRead has List, View, and Refresh, but not mutating or execute actions
    proj_reader = DummyUser(permissions=[Read])
    assert check_user_permission(proj_reader, Read)
    assert check_user_permission(proj_reader, List)
    assert check_user_permission(proj_reader, View)
    assert check_user_permission(proj_reader, CertificateDetails)
    assert check_user_permission(proj_reader, DownloadCert)
    assert check_user_permission(proj_reader, CertManager)
    assert check_user_permission(proj_reader, IssuerCert)
    assert check_user_permission(proj_reader, Refresh)
    assert not check_user_permission(proj_reader, Manage)
    assert not check_user_permission(proj_reader, Write)
    assert not check_user_permission(proj_reader, Create)
    assert not check_user_permission(proj_reader, Update)
    assert not check_user_permission(proj_reader, Delete)
    assert not check_user_permission(proj_reader, Execute)
    assert not check_user_permission(proj_reader, RenewCertificate)

    # 4. User with RenewCertificate can renew but cannot create or delete
    renewer = DummyUser(permissions=[RenewCertificate])
    assert check_user_permission(renewer, RenewCertificate)
    assert not check_user_permission(renewer, List)
    assert not check_user_permission(renewer, Create)
    assert not check_user_permission(renewer, Delete)

    # 5. Default authenticated user (with FwRead) can list and view projects
    default_user = DummyUser()
    assert check_user_permission(default_user, List)
    assert check_user_permission(default_user, View)
    assert check_user_permission(default_user, Refresh)
    assert check_user_permission(default_user, CertificateDetails)
    assert not check_user_permission(default_user, Create)
    assert not check_user_permission(default_user, RenewCertificate)


def test_project_endpoints_enforce_permissions(client: TestClient):
    """Verify project endpoints enforce permissions via HTTP API."""
    settings.enable_auth = True
    with client as c:
        admin_headers = _get_superadmin_headers(c)
        cluster_id = _create_k8s_cluster(c, admin_headers)
        reg_headers = _create_and_login_user(c, admin_headers, "regular_dave")

        # 1. Regular user cannot create project
        resp = c.post(
            "/api/v1/projects",
            json={"name": "test-perm-proj", "title": "Test Perm Proj", "k8s_cluster_id": cluster_id},
            headers=reg_headers,
        )
        assert resp.status_code == 403
        assert "Permission denied" in resp.text

        # 2. Superadmin can create project
        resp = c.post(
            "/api/v1/projects",
            json={"name": "test-perm-proj", "title": "Test Perm Proj", "k8s_cluster_id": cluster_id},
            headers=admin_headers,
        )
        assert resp.status_code == 200, resp.text
        proj_id = resp.json()["data"]["id"]

        # 3. Regular user can view project
        resp = c.get(f"/api/v1/projects/{proj_id}", headers=reg_headers)
        assert resp.status_code == 200

        # 4. Regular user can list projects
        resp = c.get("/api/v1/projects", headers=reg_headers)
        assert resp.status_code == 200

        # 5. Regular user cannot update project
        resp = c.put(
            f"/api/v1/projects/{proj_id}",
            json={"title": "Updated Title"},
            headers=reg_headers,
        )
        assert resp.status_code == 403

        # 6. Regular user cannot delete project
        resp = c.delete(
            f"/api/v1/projects/{proj_id}",
            headers={"X-RESOURCE-NAME": "test-perm-proj", **reg_headers},
        )
        assert resp.status_code == 403

        # 7. Regular user can trigger refresh (Refresh is child of View)
        resp = c.post(f"/api/v1/projects/{proj_id}/_refresh", headers=reg_headers)
        assert resp.status_code == 200


def test_project_endpoints_with_granted_permissions(client: TestClient):
    """Verify users with granted service permissions can access allowed endpoints."""
    settings.enable_auth = True
    with client as c:
        admin_headers = _get_superadmin_headers(c)
        cluster_id = _create_k8s_cluster(c, admin_headers)
        manager_headers = _create_and_login_user(c, admin_headers, "proj_manager")
        reader_headers = _create_and_login_user(c, admin_headers, "proj_reader")
        refresher_headers = _create_and_login_user(c, admin_headers, "refresher_user")

        def _mock_perms(custom_perms):
            def _get(u, *args, **kwargs):
                if getattr(u, "is_superadmin", False):
                    return [All]
                return custom_perms
            return _get

        # 1. User with Manage permission (full project control)
        with patch("mindweaver.fw.permission.get_user_permissions", side_effect=_mock_perms([Manage])):
            # Can create project
            resp = c.post(
                "/api/v1/projects",
                json={"name": "manager-proj", "title": "Manager Proj", "k8s_cluster_id": cluster_id},
                headers=manager_headers,
            )
            assert resp.status_code == 200, resp.text
            proj_id = resp.json()["data"]["id"]

            # Can update project
            resp = c.put(
                f"/api/v1/projects/{proj_id}",
                json={"title": "Updated Manager Proj"},
                headers=manager_headers,
            )
            assert resp.status_code == 200

            # Can trigger refresh
            resp = c.post(f"/api/v1/projects/{proj_id}/_refresh", headers=manager_headers)
            assert resp.status_code == 200

            # Can delete project
            resp = c.delete(
                f"/api/v1/projects/{proj_id}",
                headers={"X-RESOURCE-NAME": "manager-proj", **manager_headers},
            )
            assert resp.status_code == 200

        # 2. User with Read permission (read-only control)
        # Create project as admin
        p_resp = c.post(
            "/api/v1/projects",
            json={"name": "view-target", "title": "View Target", "k8s_cluster_id": cluster_id},
            headers=admin_headers,
        )
        assert p_resp.status_code == 200
        view_target_id = p_resp.json()["data"]["id"]

        with patch("mindweaver.fw.permission.get_user_permissions", side_effect=_mock_perms([Read])):
            # Can list projects
            resp = c.get("/api/v1/projects", headers=reader_headers)
            assert resp.status_code == 200

            # Can view project
            resp = c.get(f"/api/v1/projects/{view_target_id}", headers=reader_headers)
            assert resp.status_code == 200

            # CANNOT create project
            resp = c.post(
                "/api/v1/projects",
                json={"name": "illegal-proj", "title": "Illegal", "k8s_cluster_id": cluster_id},
                headers=reader_headers,
            )
            assert resp.status_code == 403

            # CANNOT update project
            resp = c.put(
                f"/api/v1/projects/{view_target_id}",
                json={"title": "Updated by viewer"},
                headers=reader_headers,
            )
            assert resp.status_code == 403

            # CANNOT delete project
            resp = c.delete(
                f"/api/v1/projects/{view_target_id}",
                headers={"X-RESOURCE-NAME": "view-target", **reader_headers},
            )
            assert resp.status_code == 403

            # CAN refresh project (Refresh is a view type of permission)
            resp = c.post(f"/api/v1/projects/{view_target_id}/_refresh", headers=reader_headers)
            assert resp.status_code == 200

        # 3. User with only Refresh permission
        # Create project as admin
        p_resp = c.post(
            "/api/v1/projects",
            json={"name": "refresh-target", "title": "Refresh Target", "k8s_cluster_id": cluster_id},
            headers=admin_headers,
        )
        assert p_resp.status_code == 200
        target_id = p_resp.json()["data"]["id"]

        with patch("mindweaver.fw.permission.get_user_permissions", side_effect=_mock_perms([Refresh])):
            # Refresher cannot create project
            resp = c.post(
                "/api/v1/projects",
                json={"name": "illegal-proj", "title": "Illegal", "k8s_cluster_id": cluster_id},
                headers=refresher_headers,
            )
            assert resp.status_code == 403

            # Refresher CAN refresh project
            resp = c.post(f"/api/v1/projects/{target_id}/_refresh", headers=refresher_headers)
            assert resp.status_code == 200
