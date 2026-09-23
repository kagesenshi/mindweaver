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
from mindweaver.service.k8s_cluster.permission import (
    Manage,
    ManageK8sCluster,
    K8sCluster,
    Read,
    List,
    View,
    Write,
    Create,
    Update,
    Delete,
    Execute,
    Refresh,
    ManageK8sClusterPermission,
    K8sClusterPermission,
    K8sClusterRead,
    K8sClusterList,
    K8sClusterView,
    K8sClusterWrite,
    K8sClusterCreate,
    K8sClusterUpdate,
    K8sClusterDelete,
    K8sClusterExecute,
    K8sClusterRefresh,
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


def test_k8s_cluster_permission_hierarchy():
    """Verify K8sCluster permission classes inherit correctly from All, Permission, and fw classes."""
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

    # Refresh hierarchy (inherits from View)
    assert issubclass(Refresh, View)
    assert issubclass(Refresh, Read)
    assert issubclass(Refresh, Manage)
    assert issubclass(Refresh, FwView)

    # Aliases
    assert ManageK8sCluster is Manage
    assert ManageK8sClusterPermission is Manage
    assert K8sCluster is Manage
    assert K8sClusterPermission is Manage
    assert K8sClusterRead is Read
    assert K8sClusterList is List
    assert K8sClusterView is View
    assert K8sClusterWrite is Write
    assert K8sClusterCreate is Create
    assert K8sClusterUpdate is Update
    assert K8sClusterDelete is Delete
    assert K8sClusterExecute is Execute
    assert K8sClusterRefresh is Refresh


def test_k8s_cluster_permission_string_registration():
    """Verify that K8sCluster permission names are registered in _NAME_TO_PERMISSION via init_subclass."""
    assert _NAME_TO_PERMISSION.get("k8s_cluster:manage") is Manage
    assert _NAME_TO_PERMISSION.get("k8s_cluster:read") is Read
    assert _NAME_TO_PERMISSION.get("k8s_cluster:list") is List
    assert _NAME_TO_PERMISSION.get("k8s_cluster:view") is View
    assert _NAME_TO_PERMISSION.get("k8s_cluster:write") is Write
    assert _NAME_TO_PERMISSION.get("k8s_cluster:create") is Create
    assert _NAME_TO_PERMISSION.get("k8s_cluster:update") is Update
    assert _NAME_TO_PERMISSION.get("k8s_cluster:delete") is Delete
    assert _NAME_TO_PERMISSION.get("k8s_cluster:execute") is Execute
    assert _NAME_TO_PERMISSION.get("k8s_cluster:refresh") is Refresh
    # Verify removed view_k8s_cluster is not registered
    assert "k8s_cluster:view_k8s_cluster" not in _NAME_TO_PERMISSION
    assert "k8s_cluster" not in _NAME_TO_PERMISSION
    assert "manage_k8s_cluster" not in _NAME_TO_PERMISSION


def test_k8s_cluster_check_user_permission_rules():
    """Verify check_user_permission evaluates service permissions accurately."""
    # 1. Superadmin has everything
    superadmin = DummyUser(is_superadmin=True)
    assert check_user_permission(superadmin, Manage)
    assert check_user_permission(superadmin, Read)
    assert check_user_permission(superadmin, List)
    assert check_user_permission(superadmin, Create)
    assert check_user_permission(superadmin, Refresh)

    # 2. User with Manage permission has all k8s cluster actions
    cluster_admin = DummyUser(permissions=[Manage])
    assert check_user_permission(cluster_admin, Manage)
    assert check_user_permission(cluster_admin, Read)
    assert check_user_permission(cluster_admin, List)
    assert check_user_permission(cluster_admin, View)
    assert check_user_permission(cluster_admin, Create)
    assert check_user_permission(cluster_admin, Update)
    assert check_user_permission(cluster_admin, Delete)
    assert check_user_permission(cluster_admin, Refresh)

    # 3. User with K8sClusterRead has List, View, and Refresh, but not mutating or execute actions
    cluster_reader = DummyUser(permissions=[Read])
    assert check_user_permission(cluster_reader, Read)
    assert check_user_permission(cluster_reader, List)
    assert check_user_permission(cluster_reader, View)
    assert check_user_permission(cluster_reader, Refresh)
    assert not check_user_permission(cluster_reader, Manage)
    assert not check_user_permission(cluster_reader, Write)
    assert not check_user_permission(cluster_reader, Create)
    assert not check_user_permission(cluster_reader, Update)
    assert not check_user_permission(cluster_reader, Delete)
    assert not check_user_permission(cluster_reader, Execute)

    # 4. User with Refresh can refresh status but cannot do other actions
    refresher = DummyUser(permissions=[Refresh])
    assert check_user_permission(refresher, Refresh)
    assert not check_user_permission(refresher, List)
    assert not check_user_permission(refresher, Create)
    assert not check_user_permission(refresher, Delete)

    # 5. Default authenticated user (with FwRead) can list, view, and refresh k8s clusters
    default_user = DummyUser()
    assert check_user_permission(default_user, List)
    assert check_user_permission(default_user, View)
    assert check_user_permission(default_user, Refresh)
    assert not check_user_permission(default_user, Create)


def test_k8s_cluster_endpoints_enforce_permissions(client: TestClient):
    """Verify k8s cluster endpoints enforce permissions via HTTP API."""
    settings.enable_auth = True
    with client as c:
        admin_headers = _get_superadmin_headers(c)
        reg_headers = _create_and_login_user(c, admin_headers, "regular_charlie")

        # 1. Regular user cannot create k8s cluster
        resp = c.post(
            "/api/v1/k8s_clusters",
            json={
                "name": "test-cluster-perm",
                "title": "Test Perm K8s Cluster",
                "cluster_type": "generic",
                "ingress_mode": "nodeport",
                "is_active": True,
            },
            headers=reg_headers,
        )
        assert resp.status_code == 403
        assert "Permission denied" in resp.text

        # 2. Superadmin can create k8s cluster
        resp = c.post(
            "/api/v1/k8s_clusters",
            json={
                "name": "test-cluster-perm",
                "title": "Test Perm K8s Cluster",
                "cluster_type": "generic",
                "ingress_mode": "nodeport",
                "is_active": True,
            },
            headers=admin_headers,
        )
        assert resp.status_code == 200, resp.text
        cluster_id = resp.json()["data"]["id"]

        # 3. Regular user can view k8s cluster
        resp = c.get(
            f"/api/v1/k8s_clusters/{cluster_id}",
            headers=reg_headers,
        )
        assert resp.status_code == 200

        # 4. Regular user can list k8s clusters
        resp = c.get(
            "/api/v1/k8s_clusters",
            headers=reg_headers,
        )
        assert resp.status_code == 200

        # 5. Regular user cannot update k8s cluster
        resp = c.put(
            f"/api/v1/k8s_clusters/{cluster_id}",
            json={"title": "Updated Title"},
            headers=reg_headers,
        )
        assert resp.status_code == 403

        # 6. Regular user cannot delete k8s cluster
        resp = c.delete(
            f"/api/v1/k8s_clusters/{cluster_id}",
            headers={
                "X-RESOURCE-NAME": "test-cluster-perm",
                **reg_headers,
            },
        )
        assert resp.status_code == 403

        # 7. Regular user can refresh k8s cluster status (Refresh is child of View)
        with patch("mindweaver.service.k8s_cluster.views.K8sClusterService.poll_status", AsyncMock(return_value={"healthy": True})):
            resp = c.post(
                f"/api/v1/k8s_clusters/{cluster_id}/_refresh",
                headers=reg_headers,
            )
            assert resp.status_code == 200


def test_k8s_cluster_endpoints_with_granted_permissions(client: TestClient):
    """Verify users with granted service permissions can access allowed endpoints."""
    settings.enable_auth = True
    with client as c:
        admin_headers = _get_superadmin_headers(c)
        manager_headers = _create_and_login_user(c, admin_headers, "cluster_manager")
        reader_headers = _create_and_login_user(c, admin_headers, "cluster_reader")
        refresher_headers = _create_and_login_user(c, admin_headers, "cluster_refresher")

        def _mock_perms(custom_perms):
            def _get(u, *args, **kwargs):
                if getattr(u, "is_superadmin", False):
                    return [All]
                return custom_perms
            return _get

        # 1. User with Manage permission (full control)
        with patch("mindweaver.fw.permission.get_user_permissions", side_effect=_mock_perms([Manage])):
            # Can create
            resp = c.post(
                "/api/v1/k8s_clusters",
                json={
                    "name": "mgr-cluster",
                    "title": "Mgr K8s Cluster",
                    "cluster_type": "generic",
                    "ingress_mode": "nodeport",
                    "is_active": True,
                },
                headers=manager_headers,
            )
            assert resp.status_code == 200, resp.text
            created_id = resp.json()["data"]["id"]

            # Can update
            resp = c.put(
                f"/api/v1/k8s_clusters/{created_id}",
                json={"title": "Updated Mgr Cluster"},
                headers=manager_headers,
            )
            assert resp.status_code == 200

            # Can refresh status
            with patch("mindweaver.service.k8s_cluster.views.K8sClusterService.poll_status", AsyncMock(return_value={"healthy": True})):
                resp = c.post(
                    f"/api/v1/k8s_clusters/{created_id}/_refresh",
                    headers=manager_headers,
                )
                assert resp.status_code == 200

            # Can delete
            resp = c.delete(
                f"/api/v1/k8s_clusters/{created_id}",
                headers={
                    "X-RESOURCE-NAME": "mgr-cluster",
                    **manager_headers,
                },
            )
            assert resp.status_code == 200

        # 2. User with Read permission (read-only control)
        # Create a cluster as admin
        r_resp = c.post(
            "/api/v1/k8s_clusters",
            json={
                "name": "view-cluster-target",
                "title": "View Target Cluster",
                "cluster_type": "generic",
                "ingress_mode": "nodeport",
                "is_active": True,
            },
            headers=admin_headers,
        )
        assert r_resp.status_code == 200
        target_cluster_id = r_resp.json()["data"]["id"]

        with patch("mindweaver.fw.permission.get_user_permissions", side_effect=_mock_perms([Read])):
            # Can list
            resp = c.get(
                "/api/v1/k8s_clusters",
                headers=reader_headers,
            )
            assert resp.status_code == 200

            # Can view
            resp = c.get(
                f"/api/v1/k8s_clusters/{target_cluster_id}",
                headers=reader_headers,
            )
            assert resp.status_code == 200

            # Can refresh
            with patch("mindweaver.service.k8s_cluster.views.K8sClusterService.poll_status", AsyncMock(return_value={"healthy": True})):
                resp = c.post(
                    f"/api/v1/k8s_clusters/{target_cluster_id}/_refresh",
                    headers=reader_headers,
                )
                assert resp.status_code == 200

            # CANNOT create
            resp = c.post(
                "/api/v1/k8s_clusters",
                json={
                    "name": "illegal-cluster-viewer",
                    "title": "Illegal",
                    "cluster_type": "generic",
                    "ingress_mode": "nodeport",
                    "is_active": True,
                },
                headers=reader_headers,
            )
            assert resp.status_code == 403

            # CANNOT update
            resp = c.put(
                f"/api/v1/k8s_clusters/{target_cluster_id}",
                json={"title": "Updated by viewer"},
                headers=reader_headers,
            )
            assert resp.status_code == 403

            # CANNOT delete
            resp = c.delete(
                f"/api/v1/k8s_clusters/{target_cluster_id}",
                headers={
                    "X-RESOURCE-NAME": "view-cluster-target",
                    **reader_headers,
                },
            )
            assert resp.status_code == 403

        # 3. User with only Refresh permission
        with patch("mindweaver.fw.permission.get_user_permissions", side_effect=_mock_perms([Refresh])):
            # Refresher cannot create
            resp = c.post(
                "/api/v1/k8s_clusters",
                json={
                    "name": "illegal-cluster-refresher",
                    "title": "Illegal",
                    "cluster_type": "generic",
                    "ingress_mode": "nodeport",
                    "is_active": True,
                },
                headers=refresher_headers,
            )
            assert resp.status_code == 403

            # Refresher CAN refresh
            with patch("mindweaver.service.k8s_cluster.views.K8sClusterService.poll_status", AsyncMock(return_value={"healthy": True})):
                resp = c.post(
                    f"/api/v1/k8s_clusters/{target_cluster_id}/_refresh",
                    headers=refresher_headers,
                )
                assert resp.status_code == 200
