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
from mindweaver.service.container_registry.permission import (
    Manage,
    ManageContainerRegistry,
    ContainerRegistry,
    Read,
    List,
    View,
    Write,
    Create,
    Update,
    Delete,
    Execute,
    TestConnection,
    ManageContainerRegistryPermission,
    ContainerRegistryPermission,
    ContainerRegistryRead,
    ContainerRegistryList,
    ContainerRegistryView,
    ContainerRegistryWrite,
    ContainerRegistryCreate,
    ContainerRegistryUpdate,
    ContainerRegistryDelete,
    ContainerRegistryExecute,
    ContainerRegistryTestConnection,
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


def test_container_registry_permission_hierarchy():
    """Verify ContainerRegistry permission classes inherit correctly from All, Permission, and fw classes."""
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
    assert issubclass(TestConnection, Execute)
    assert not issubclass(TestConnection, Read)

    # Aliases
    assert ManageContainerRegistry is Manage
    assert ManageContainerRegistryPermission is Manage
    assert ContainerRegistry is Manage
    assert ContainerRegistryPermission is Manage
    assert ContainerRegistryRead is Read
    assert ContainerRegistryList is List
    assert ContainerRegistryView is View
    assert ContainerRegistryWrite is Write
    assert ContainerRegistryCreate is Create
    assert ContainerRegistryUpdate is Update
    assert ContainerRegistryDelete is Delete
    assert ContainerRegistryExecute is Execute
    assert ContainerRegistryTestConnection is TestConnection


def test_container_registry_permission_string_registration():
    """Verify that ContainerRegistry permission names are registered in _NAME_TO_PERMISSION via init_subclass."""
    assert _NAME_TO_PERMISSION.get("container_registry:manage") is Manage
    assert _NAME_TO_PERMISSION.get("container_registry:read") is Read
    assert _NAME_TO_PERMISSION.get("container_registry:list") is List
    assert _NAME_TO_PERMISSION.get("container_registry:view") is View
    assert _NAME_TO_PERMISSION.get("container_registry:write") is Write
    assert _NAME_TO_PERMISSION.get("container_registry:create") is Create
    assert _NAME_TO_PERMISSION.get("container_registry:update") is Update
    assert _NAME_TO_PERMISSION.get("container_registry:delete") is Delete
    assert _NAME_TO_PERMISSION.get("container_registry:execute") is Execute
    assert _NAME_TO_PERMISSION.get("container_registry:test_connection") is TestConnection
    # Verify removed view_container_registry is not registered
    assert "container_registry:view_container_registry" not in _NAME_TO_PERMISSION
    assert "container_registry" not in _NAME_TO_PERMISSION
    assert "manage_container_registry" not in _NAME_TO_PERMISSION


def test_container_registry_check_user_permission_rules():
    """Verify check_user_permission evaluates service permissions accurately."""
    # 1. Superadmin has everything
    superadmin = DummyUser(is_superadmin=True)
    assert check_user_permission(superadmin, Manage)
    assert check_user_permission(superadmin, Read)
    assert check_user_permission(superadmin, List)
    assert check_user_permission(superadmin, Create)
    assert check_user_permission(superadmin, TestConnection)

    # 2. User with Manage permission has all container registry actions
    reg_admin = DummyUser(permissions=[Manage])
    assert check_user_permission(reg_admin, Manage)
    assert check_user_permission(reg_admin, Read)
    assert check_user_permission(reg_admin, List)
    assert check_user_permission(reg_admin, View)
    assert check_user_permission(reg_admin, Create)
    assert check_user_permission(reg_admin, Update)
    assert check_user_permission(reg_admin, Delete)
    assert check_user_permission(reg_admin, TestConnection)

    # 3. User with ContainerRegistryRead has List and View, but not mutating or execute actions
    reg_reader = DummyUser(permissions=[Read])
    assert check_user_permission(reg_reader, Read)
    assert check_user_permission(reg_reader, List)
    assert check_user_permission(reg_reader, View)
    assert not check_user_permission(reg_reader, Manage)
    assert not check_user_permission(reg_reader, Write)
    assert not check_user_permission(reg_reader, Create)
    assert not check_user_permission(reg_reader, Update)
    assert not check_user_permission(reg_reader, Delete)
    assert not check_user_permission(reg_reader, Execute)
    assert not check_user_permission(reg_reader, TestConnection)

    # 4. User with ContainerRegistryTestConnection can test connection but cannot do other actions
    tester = DummyUser(permissions=[TestConnection])
    assert check_user_permission(tester, TestConnection)
    assert not check_user_permission(tester, List)
    assert not check_user_permission(tester, Create)
    assert not check_user_permission(tester, Delete)

    # 5. Default authenticated user (with FwRead) can list and view container registries
    default_user = DummyUser()
    assert check_user_permission(default_user, List)
    assert check_user_permission(default_user, View)
    assert not check_user_permission(default_user, Create)
    assert not check_user_permission(default_user, TestConnection)


def test_container_registry_endpoints_enforce_permissions(client: TestClient, test_project):
    """Verify container registry endpoints enforce permissions via HTTP API."""
    settings.enable_auth = True
    with client as c:
        admin_headers = _get_superadmin_headers(c)
        reg_headers = _create_and_login_user(c, admin_headers, "regular_alice")
        proj_id = test_project["id"]

        # 1. Regular user cannot create container registry
        resp = c.post(
            "/api/v1/container_registries",
            json={
                "name": "test-reg-perm",
                "title": "Test Perm Container Registry",
                "url": "docker.io",
                "username": "user",
                "password": "pwd",
                "project_id": proj_id,
            },
            headers={"X-Project-ID": str(proj_id), **reg_headers},
        )
        assert resp.status_code == 403
        assert "Permission denied" in resp.text

        # 2. Superadmin can create container registry
        resp = c.post(
            "/api/v1/container_registries",
            json={
                "name": "test-reg-perm",
                "title": "Test Perm Container Registry",
                "url": "docker.io",
                "username": "user",
                "password": "pwd",
                "project_id": proj_id,
            },
            headers={"X-Project-ID": str(proj_id), **admin_headers},
        )
        assert resp.status_code == 200, resp.text
        reg_id = resp.json()["data"]["id"]

        # 3. Regular user can view container registry
        resp = c.get(
            f"/api/v1/container_registries/{reg_id}",
            headers={"X-Project-ID": str(proj_id), **reg_headers},
        )
        assert resp.status_code == 200

        # 4. Regular user can list container registries
        resp = c.get(
            "/api/v1/container_registries",
            headers={"X-Project-ID": str(proj_id), **reg_headers},
        )
        assert resp.status_code == 200

        # 5. Regular user cannot update container registry
        resp = c.put(
            f"/api/v1/container_registries/{reg_id}",
            json={"title": "Updated Title"},
            headers={"X-Project-ID": str(proj_id), **reg_headers},
        )
        assert resp.status_code == 403

        # 6. Regular user cannot delete container registry
        resp = c.delete(
            f"/api/v1/container_registries/{reg_id}",
            headers={
                "X-RESOURCE-NAME": "test-reg-perm",
                "X-Project-ID": str(proj_id),
                **reg_headers,
            },
        )
        assert resp.status_code == 403

        # 7. Regular user cannot trigger test connection
        resp = c.post(
            "/api/v1/container_registries/_test-connection",
            json={"url": "docker.io"},
            headers={"X-Project-ID": str(proj_id), **reg_headers},
        )
        assert resp.status_code == 403
        assert "Permission denied for 'container_registry:test_connection'" in resp.text


def test_container_registry_endpoints_with_granted_permissions(client: TestClient, test_project):
    """Verify users with granted service permissions can access allowed endpoints."""
    settings.enable_auth = True
    with client as c:
        admin_headers = _get_superadmin_headers(c)
        proj_id = test_project["id"]
        manager_headers = _create_and_login_user(c, admin_headers, "reg_manager")
        reader_headers = _create_and_login_user(c, admin_headers, "reg_reader")
        tester_headers = _create_and_login_user(c, admin_headers, "conn_tester")

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
                "/api/v1/container_registries",
                json={
                    "name": "mgr-reg",
                    "title": "Mgr Container Registry",
                    "url": "docker.io",
                    "username": "u",
                    "password": "p",
                    "project_id": proj_id,
                },
                headers={"X-Project-ID": str(proj_id), **manager_headers},
            )
            assert resp.status_code == 200, resp.text
            created_id = resp.json()["data"]["id"]

            # Can update
            resp = c.put(
                f"/api/v1/container_registries/{created_id}",
                json={"title": "Updated Mgr Registry"},
                headers={"X-Project-ID": str(proj_id), **manager_headers},
            )
            assert resp.status_code == 200

            # Can test connection
            with patch("mindweaver.service.container_registry.views.run_oci_login_check", AsyncMock(return_value=(True, "OK"))):
                resp = c.post(
                    "/api/v1/container_registries/_test-connection",
                    json={"url": "docker.io", "username": "u", "password": "p"},
                    headers={"X-Project-ID": str(proj_id), **manager_headers},
                )
                assert resp.status_code == 200
                assert resp.json()["status"] == "success"

            # Can delete
            resp = c.delete(
                f"/api/v1/container_registries/{created_id}",
                headers={
                    "X-RESOURCE-NAME": "mgr-reg",
                    "X-Project-ID": str(proj_id),
                    **manager_headers,
                },
            )
            assert resp.status_code == 200

        # 2. User with Read permission (read-only control)
        # Create a registry as admin
        r_resp = c.post(
            "/api/v1/container_registries",
            json={
                "name": "view-reg-target",
                "title": "View Target",
                "url": "docker.io",
                "username": "u",
                "password": "p",
                "project_id": proj_id,
            },
            headers={"X-Project-ID": str(proj_id), **admin_headers},
        )
        assert r_resp.status_code == 200
        target_reg_id = r_resp.json()["data"]["id"]

        with patch("mindweaver.fw.permission.get_user_permissions", side_effect=_mock_perms([Read])):
            # Can list
            resp = c.get(
                "/api/v1/container_registries",
                headers={"X-Project-ID": str(proj_id), **reader_headers},
            )
            assert resp.status_code == 200

            # Can view
            resp = c.get(
                f"/api/v1/container_registries/{target_reg_id}",
                headers={"X-Project-ID": str(proj_id), **reader_headers},
            )
            assert resp.status_code == 200

            # CANNOT create
            resp = c.post(
                "/api/v1/container_registries",
                json={
                    "name": "illegal-reg-viewer",
                    "title": "Illegal",
                    "url": "docker.io",
                    "username": "u",
                    "password": "p",
                    "project_id": proj_id,
                },
                headers={"X-Project-ID": str(proj_id), **reader_headers},
            )
            assert resp.status_code == 403

            # CANNOT update
            resp = c.put(
                f"/api/v1/container_registries/{target_reg_id}",
                json={"title": "Updated by viewer"},
                headers={"X-Project-ID": str(proj_id), **reader_headers},
            )
            assert resp.status_code == 403

            # CANNOT test connection
            resp = c.post(
                "/api/v1/container_registries/_test-connection",
                json={"url": "docker.io", "username": "u", "password": "p"},
                headers={"X-Project-ID": str(proj_id), **reader_headers},
            )
            assert resp.status_code == 403

            # CANNOT delete
            resp = c.delete(
                f"/api/v1/container_registries/{target_reg_id}",
                headers={
                    "X-RESOURCE-NAME": "view-reg-target",
                    "X-Project-ID": str(proj_id),
                    **reader_headers,
                },
            )
            assert resp.status_code == 403

        # 3. User with only TestConnection permission
        with patch("mindweaver.fw.permission.get_user_permissions", side_effect=_mock_perms([TestConnection])):
            # Tester cannot create
            resp = c.post(
                "/api/v1/container_registries",
                json={
                    "name": "illegal-reg-tester",
                    "title": "Illegal",
                    "url": "docker.io",
                    "username": "u",
                    "password": "p",
                    "project_id": proj_id,
                },
                headers={"X-Project-ID": str(proj_id), **tester_headers},
            )
            assert resp.status_code == 403

            # Tester CAN test connection
            with patch("mindweaver.service.container_registry.views.run_oci_login_check", AsyncMock(return_value=(True, "OK"))):
                resp = c.post(
                    "/api/v1/container_registries/_test-connection",
                    json={"url": "docker.io", "username": "u", "password": "p"},
                    headers={"X-Project-ID": str(proj_id), **tester_headers},
                )
                assert resp.status_code == 200
                assert resp.json()["status"] == "success"
