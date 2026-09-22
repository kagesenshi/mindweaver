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
    ManageK8sCluster,
    ViewK8sCluster,
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
    ViewK8sClusterPermission,
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
    assert issubclass(ManageK8sCluster, Permission)
    assert issubclass(ManageK8sCluster, All)

    # ViewK8sCluster hierarchy
    assert issubclass(ViewK8sCluster, ManageK8sCluster)
    assert issubclass(ViewK8sCluster, Permission)

    # Read hierarchy (inherits from ViewK8sCluster and FwRead)
    assert issubclass(Read, ViewK8sCluster)
    assert issubclass(Read, ManageK8sCluster)
    assert issubclass(Read, FwRead)
    assert issubclass(List, Read)
    assert issubclass(List, ViewK8sCluster)
    assert issubclass(List, FwList)
    assert issubclass(View, Read)
    assert issubclass(View, ViewK8sCluster)
    assert issubclass(View, FwView)

    # Write hierarchy (inherits from ManageK8sCluster, NOT ViewK8sCluster)
    assert issubclass(Write, ManageK8sCluster)
    assert not issubclass(Write, ViewK8sCluster)
    assert issubclass(Write, FwWrite)
    assert issubclass(Create, Write)
    assert not issubclass(Create, ViewK8sCluster)
    assert issubclass(Create, FwCreate)
    assert issubclass(Update, Write)
    assert not issubclass(Update, ViewK8sCluster)
    assert issubclass(Update, FwUpdate)
    assert issubclass(Delete, Write)
    assert not issubclass(Delete, ViewK8sCluster)
    assert issubclass(Delete, FwDelete)

    # Execute hierarchy (inherits from ManageK8sCluster, NOT ViewK8sCluster)
    assert issubclass(Execute, ManageK8sCluster)
    assert not issubclass(Execute, ViewK8sCluster)
    assert issubclass(Execute, FwExecute)

    # Refresh hierarchy (inherits from View)
    assert issubclass(Refresh, View)
    assert issubclass(Refresh, Read)
    assert issubclass(Refresh, ViewK8sCluster)
    assert issubclass(Refresh, FwView)

    # Aliases
    assert ManageK8sClusterPermission is ManageK8sCluster
    assert ViewK8sClusterPermission is ViewK8sCluster
    assert K8sCluster is ManageK8sCluster
    assert K8sClusterPermission is ManageK8sCluster
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
    assert _NAME_TO_PERMISSION.get("k8s_cluster:manage") is ManageK8sCluster
    assert _NAME_TO_PERMISSION.get("k8s_cluster:view_k8s_cluster") is ViewK8sCluster
    assert _NAME_TO_PERMISSION.get("k8s_cluster:read") is Read
    assert _NAME_TO_PERMISSION.get("k8s_cluster:list") is List
    assert _NAME_TO_PERMISSION.get("k8s_cluster:view") is View
    assert _NAME_TO_PERMISSION.get("k8s_cluster:write") is Write
    assert _NAME_TO_PERMISSION.get("k8s_cluster:create") is Create
    assert _NAME_TO_PERMISSION.get("k8s_cluster:update") is Update
    assert _NAME_TO_PERMISSION.get("k8s_cluster:delete") is Delete
    assert _NAME_TO_PERMISSION.get("k8s_cluster:execute") is Execute
    assert _NAME_TO_PERMISSION.get("k8s_cluster:refresh") is Refresh
    # Verify manual aliases are not registered
    assert "k8s_cluster" not in _NAME_TO_PERMISSION
    assert "manage_k8s_cluster" not in _NAME_TO_PERMISSION
    assert "view_k8s_cluster" not in _NAME_TO_PERMISSION


def test_k8s_cluster_check_user_permission_rules():
    """Verify check_user_permission evaluates service permissions accurately."""
    # 1. Superadmin has everything
    superadmin = DummyUser(is_superadmin=True)
    assert check_user_permission(superadmin, ManageK8sCluster)
    assert check_user_permission(superadmin, ViewK8sCluster)
    assert check_user_permission(superadmin, List)
    assert check_user_permission(superadmin, Create)
    assert check_user_permission(superadmin, Execute)
    assert check_user_permission(superadmin, Refresh)

    # 2. User with ManageK8sCluster permission has all k8s cluster actions
    cluster_admin = DummyUser(permissions=[ManageK8sCluster])
    assert check_user_permission(cluster_admin, ManageK8sCluster)
    assert check_user_permission(cluster_admin, ViewK8sCluster)
    assert check_user_permission(cluster_admin, List)
    assert check_user_permission(cluster_admin, View)
    assert check_user_permission(cluster_admin, Create)
    assert check_user_permission(cluster_admin, Update)
    assert check_user_permission(cluster_admin, Delete)
    assert check_user_permission(cluster_admin, Execute)
    assert check_user_permission(cluster_admin, Refresh)

    # 3. User with ViewK8sCluster permission has view-type actions ONLY
    cluster_viewer = DummyUser(permissions=[ViewK8sCluster])
    assert check_user_permission(cluster_viewer, ViewK8sCluster)
    assert check_user_permission(cluster_viewer, List)
    assert check_user_permission(cluster_viewer, View)
    assert check_user_permission(cluster_viewer, Refresh)
    # Mutating / operational actions MUST be denied
    assert not check_user_permission(cluster_viewer, ManageK8sCluster)
    assert not check_user_permission(cluster_viewer, Write)
    assert not check_user_permission(cluster_viewer, Create)
    assert not check_user_permission(cluster_viewer, Update)
    assert not check_user_permission(cluster_viewer, Delete)
    assert not check_user_permission(cluster_viewer, Execute)

    # 4. User with K8sClusterRead has List, View, and Refresh, but not mutating or execute actions
    cluster_reader = DummyUser(permissions=[Read])
    assert check_user_permission(cluster_reader, List)
    assert check_user_permission(cluster_reader, View)
    assert check_user_permission(cluster_reader, Refresh)
    assert not check_user_permission(cluster_reader, Create)
    assert not check_user_permission(cluster_reader, Update)
    assert not check_user_permission(cluster_reader, Delete)
    assert not check_user_permission(cluster_reader, Execute)

    # 5. User with K8sClusterExecute can execute actions but cannot do write actions
    executor = DummyUser(permissions=[Execute])
    assert check_user_permission(executor, Execute)
    assert not check_user_permission(executor, List)
    assert not check_user_permission(executor, Create)
    assert not check_user_permission(executor, Delete)

    # 6. Default authenticated user (with FwRead) can list, view, and refresh k8s clusters
    default_user = DummyUser()
    assert check_user_permission(default_user, List)
    assert check_user_permission(default_user, View)
    assert check_user_permission(default_user, Refresh)
    assert not check_user_permission(default_user, Create)
    assert not check_user_permission(default_user, Execute)


def test_k8s_cluster_endpoints_enforce_permissions(client: TestClient):
    """Verify k8s cluster endpoints enforce permissions via HTTP API."""
    settings.enable_auth = True
    with client as c:
        admin_headers = _get_superadmin_headers(c)
        reg_headers = _create_and_login_user(c, admin_headers, "regular_bob")

        # 1. Regular user cannot create k8s cluster
        resp = c.post(
            "/api/v1/k8s_clusters",
            json={
                "name": "test-cluster-perm",
                "title": "Test Perm K8s Cluster",
                "description": "Test Perm K8s Cluster",
                "type": "remote",
                "kubeconfig": "apiVersion: v1\nclusters: []",
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
                "description": "Test Perm K8s Cluster",
                "type": "remote",
                "kubeconfig": "apiVersion: v1\nclusters: []",
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

        # 5. Regular user can call refresh (since Refresh inherits from View, default auth has Read)
        with patch("mindweaver.service.k8s_cluster.service.K8sClusterService.poll_status", AsyncMock()):
            resp = c.post(
                f"/api/v1/k8s_clusters/{cluster_id}/_refresh",
                headers=reg_headers,
            )
            assert resp.status_code == 200
            assert resp.json()["status"] == "success"

        # 6. Regular user can list actions (guarded by View)
        resp = c.get(
            f"/api/v1/k8s_clusters/{cluster_id}/_actions",
            headers=reg_headers,
        )
        assert resp.status_code == 200

        # 7. Regular user cannot execute action (guarded by Execute)
        resp = c.post(
            f"/api/v1/k8s_clusters/{cluster_id}/_actions",
            json={"action": "install_argocd"},
            headers=reg_headers,
        )
        assert resp.status_code == 403
        assert "Permission denied for 'k8s_cluster:execute'" in resp.text

        # 8. Regular user cannot update k8s cluster
        resp = c.put(
            f"/api/v1/k8s_clusters/{cluster_id}",
            json={"description": "Updated Description"},
            headers=reg_headers,
        )
        assert resp.status_code == 403

        # 9. Regular user cannot delete k8s cluster
        resp = c.delete(
            f"/api/v1/k8s_clusters/{cluster_id}",
            headers={
                "X-RESOURCE-NAME": "test-cluster-perm",
                **reg_headers,
            },
        )
        assert resp.status_code == 403


def test_k8s_cluster_endpoints_with_granted_permissions(client: TestClient):
    """Verify users with granted service permissions can access allowed endpoints."""
    settings.enable_auth = True
    with client as c:
        admin_headers = _get_superadmin_headers(c)
        manager_headers = _create_and_login_user(c, admin_headers, "cluster_manager")
        viewer_headers = _create_and_login_user(c, admin_headers, "cluster_viewer")
        executor_headers = _create_and_login_user(c, admin_headers, "cluster_executor")

        def _mock_perms(custom_perms):
            def _get(u):
                if getattr(u, "is_superadmin", False):
                    return [All]
                return custom_perms
            return _get

        # 1. User with ManageK8sCluster permission (full control)
        with patch("mindweaver.fw.permission.get_user_permissions", side_effect=_mock_perms([ManageK8sCluster])):
            # Can create
            resp = c.post(
                "/api/v1/k8s_clusters",
                json={
                    "name": "mgr-cluster",
                    "title": "Mgr Cluster",
                    "description": "Mgr Cluster",
                    "type": "remote",
                    "kubeconfig": "apiVersion: v1\nclusters: []",
                },
                headers=manager_headers,
            )
            assert resp.status_code == 200, resp.text
            created_id = resp.json()["data"]["id"]

            # Can update
            resp = c.put(
                f"/api/v1/k8s_clusters/{created_id}",
                json={"description": "Updated Mgr Cluster"},
                headers=manager_headers,
            )
            assert resp.status_code == 200

            # Can refresh
            with patch("mindweaver.service.k8s_cluster.service.K8sClusterService.poll_status", AsyncMock()):
                resp = c.post(
                    f"/api/v1/k8s_clusters/{created_id}/_refresh",
                    headers=manager_headers,
                )
                assert resp.status_code == 200

            # Can execute action
            with patch("mindweaver.tasks.k8s_cluster_status.install_argocd_task.delay"):
                resp = c.post(
                    f"/api/v1/k8s_clusters/{created_id}/_actions",
                    json={"action": "install_argocd"},
                    headers=manager_headers,
                )
                assert resp.status_code == 200
                assert resp.json()["status"] == "success"

            # Can delete
            resp = c.delete(
                f"/api/v1/k8s_clusters/{created_id}",
                headers={
                    "X-RESOURCE-NAME": "mgr-cluster",
                    **manager_headers,
                },
            )
            assert resp.status_code == 200

        # 2. User with ViewK8sCluster permission (view-only control)
        # Create a cluster as admin
        r_resp = c.post(
            "/api/v1/k8s_clusters",
            json={
                "name": "view-cluster-target",
                "title": "View Target",
                "description": "View Target",
                "type": "remote",
                "kubeconfig": "apiVersion: v1\nclusters: []",
            },
            headers=admin_headers,
        )
        assert r_resp.status_code == 200
        target_cluster_id = r_resp.json()["data"]["id"]

        with patch("mindweaver.fw.permission.get_user_permissions", side_effect=_mock_perms([ViewK8sCluster])):
            # Can list
            resp = c.get(
                "/api/v1/k8s_clusters",
                headers=viewer_headers,
            )
            assert resp.status_code == 200

            # Can view
            resp = c.get(
                f"/api/v1/k8s_clusters/{target_cluster_id}",
                headers=viewer_headers,
            )
            assert resp.status_code == 200

            # Can refresh
            with patch("mindweaver.service.k8s_cluster.service.K8sClusterService.poll_status", AsyncMock()):
                resp = c.post(
                    f"/api/v1/k8s_clusters/{target_cluster_id}/_refresh",
                    headers=viewer_headers,
                )
                assert resp.status_code == 200

            # CANNOT create
            resp = c.post(
                "/api/v1/k8s_clusters",
                json={
                    "name": "illegal-cluster-viewer",
                    "title": "Illegal",
                    "description": "Illegal",
                    "type": "remote",
                    "kubeconfig": "apiVersion: v1\nclusters: []",
                },
                headers=viewer_headers,
            )
            assert resp.status_code == 403

            # CANNOT update
            resp = c.put(
                f"/api/v1/k8s_clusters/{target_cluster_id}",
                json={"description": "Updated by viewer"},
                headers=viewer_headers,
            )
            assert resp.status_code == 403

            # CANNOT execute action
            resp = c.post(
                f"/api/v1/k8s_clusters/{target_cluster_id}/_actions",
                json={"action": "install_argocd"},
                headers=viewer_headers,
            )
            assert resp.status_code == 403

            # CANNOT delete
            resp = c.delete(
                f"/api/v1/k8s_clusters/{target_cluster_id}",
                headers={
                    "X-RESOURCE-NAME": "view-cluster-target",
                    **viewer_headers,
                },
            )
            assert resp.status_code == 403

        # 3. User with only Execute permission
        with patch("mindweaver.fw.permission.get_user_permissions", side_effect=_mock_perms([Execute])):
            # Executor cannot create
            resp = c.post(
                "/api/v1/k8s_clusters",
                json={
                    "name": "illegal-cluster-executor",
                    "title": "Illegal",
                    "description": "Illegal",
                    "type": "remote",
                    "kubeconfig": "apiVersion: v1\nclusters: []",
                },
                headers=executor_headers,
            )
            assert resp.status_code == 403

            # Executor CAN execute action
            with patch("mindweaver.tasks.k8s_cluster_status.install_argocd_task.delay"):
                resp = c.post(
                    f"/api/v1/k8s_clusters/{target_cluster_id}/_actions",
                    json={"action": "install_argocd"},
                    headers=executor_headers,
                )
                assert resp.status_code == 200
                assert resp.json()["status"] == "success"
