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
from mindweaver.service.ldap_config.permission import (
    Manage,
    ManageLdapConfig,
    LdapConfig,
    Read,
    List,
    View,
    Write,
    Create,
    Update,
    Delete,
    Execute,
    TestConnection,
    ManageLdapConfigPermission,
    LdapConfigPermission,
    LdapConfigRead,
    LdapConfigList,
    LdapConfigView,
    LdapConfigWrite,
    LdapConfigCreate,
    LdapConfigUpdate,
    LdapConfigDelete,
    LdapConfigExecute,
    LdapConfigTestConnection,
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


def test_ldap_config_permission_hierarchy():
    """Verify LdapConfig permission classes inherit correctly from All, Permission, and fw classes."""
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
    assert ManageLdapConfig is Manage
    assert ManageLdapConfigPermission is Manage
    assert LdapConfig is Manage
    assert LdapConfigPermission is Manage
    assert LdapConfigRead is Read
    assert LdapConfigList is List
    assert LdapConfigView is View
    assert LdapConfigWrite is Write
    assert LdapConfigCreate is Create
    assert LdapConfigUpdate is Update
    assert LdapConfigDelete is Delete
    assert LdapConfigExecute is Execute
    assert LdapConfigTestConnection is TestConnection


def test_ldap_config_permission_string_registration():
    """Verify that LdapConfig permission names are registered in _NAME_TO_PERMISSION via init_subclass."""
    assert _NAME_TO_PERMISSION.get("ldap_config:manage") is Manage
    assert _NAME_TO_PERMISSION.get("ldap_config:read") is Read
    assert _NAME_TO_PERMISSION.get("ldap_config:list") is List
    assert _NAME_TO_PERMISSION.get("ldap_config:view") is View
    assert _NAME_TO_PERMISSION.get("ldap_config:write") is Write
    assert _NAME_TO_PERMISSION.get("ldap_config:create") is Create
    assert _NAME_TO_PERMISSION.get("ldap_config:update") is Update
    assert _NAME_TO_PERMISSION.get("ldap_config:delete") is Delete
    assert _NAME_TO_PERMISSION.get("ldap_config:execute") is Execute
    assert _NAME_TO_PERMISSION.get("ldap_config:test_connection") is TestConnection
    # Verify manual aliases are not registered
    assert "ldap_config" not in _NAME_TO_PERMISSION
    assert "manage_ldap_config" not in _NAME_TO_PERMISSION
    assert "view_ldap_config" not in _NAME_TO_PERMISSION


def test_ldap_config_check_user_permission_rules():
    """Verify check_user_permission evaluates service permissions accurately."""
    # 1. Superadmin has everything
    superadmin = DummyUser(is_superadmin=True)
    assert check_user_permission(superadmin, Manage)
    assert check_user_permission(superadmin, Read)
    assert check_user_permission(superadmin, List)
    assert check_user_permission(superadmin, Create)
    assert check_user_permission(superadmin, TestConnection)

    # 2. User with Manage permission has all ldap config actions
    ldap_admin = DummyUser(permissions=[Manage])
    assert check_user_permission(ldap_admin, Manage)
    assert check_user_permission(ldap_admin, Read)
    assert check_user_permission(ldap_admin, List)
    assert check_user_permission(ldap_admin, View)
    assert check_user_permission(ldap_admin, Create)
    assert check_user_permission(ldap_admin, Update)
    assert check_user_permission(ldap_admin, Delete)
    assert check_user_permission(ldap_admin, TestConnection)

    # 3. User with LdapConfigRead has List and View, but not mutating or execute actions
    ldap_reader = DummyUser(permissions=[Read])
    assert check_user_permission(ldap_reader, Read)
    assert check_user_permission(ldap_reader, List)
    assert check_user_permission(ldap_reader, View)
    assert not check_user_permission(ldap_reader, Manage)
    assert not check_user_permission(ldap_reader, Write)
    assert not check_user_permission(ldap_reader, Create)
    assert not check_user_permission(ldap_reader, Update)
    assert not check_user_permission(ldap_reader, Delete)
    assert not check_user_permission(ldap_reader, Execute)
    assert not check_user_permission(ldap_reader, TestConnection)

    # 4. User with LdapConfigTestConnection can test connection but cannot do other actions
    tester = DummyUser(permissions=[TestConnection])
    assert check_user_permission(tester, TestConnection)
    assert not check_user_permission(tester, List)
    assert not check_user_permission(tester, Create)
    assert not check_user_permission(tester, Delete)

    # 5. Default authenticated user (with FwRead) can list and view ldap configs
    default_user = DummyUser()
    assert check_user_permission(default_user, List)
    assert check_user_permission(default_user, View)
    assert not check_user_permission(default_user, Create)
    assert not check_user_permission(default_user, TestConnection)


def test_ldap_config_endpoints_enforce_permissions(client: TestClient, test_project):
    """Verify ldap config endpoints enforce permissions via HTTP API."""
    settings.enable_auth = True
    with client as c:
        admin_headers = _get_superadmin_headers(c)
        reg_headers = _create_and_login_user(c, admin_headers, "regular_eve")
        proj_id = test_project["id"]

        ldap_payload = {
            "name": "test-ldap-perm",
            "title": "Test Perm LDAP",
            "server_url": "ldap://ldap.example.com",
            "bind_dn": "cn=admin,dc=example,dc=com",
            "bind_password": "supersecretpassword",
            "user_search_base": "ou=users,dc=example,dc=com",
            "user_search_filter": "(uid={0})",
            "username_attr": "uid",
            "verify_ssl": True,
            "project_id": proj_id,
        }

        # 1. Regular user cannot create ldap config
        resp = c.post(
            "/api/v1/ldap_configs",
            json=ldap_payload,
            headers={"X-Project-ID": str(proj_id), **reg_headers},
        )
        assert resp.status_code == 403
        assert "Permission denied" in resp.text

        # 2. Superadmin can create ldap config
        resp = c.post(
            "/api/v1/ldap_configs",
            json=ldap_payload,
            headers={"X-Project-ID": str(proj_id), **admin_headers},
        )
        assert resp.status_code == 200, resp.text
        config_id = resp.json()["data"]["id"]

        # 3. Regular user can view ldap config
        resp = c.get(
            f"/api/v1/ldap_configs/{config_id}",
            headers={"X-Project-ID": str(proj_id), **reg_headers},
        )
        assert resp.status_code == 200

        # 4. Regular user can list ldap configs
        resp = c.get(
            "/api/v1/ldap_configs",
            headers={"X-Project-ID": str(proj_id), **reg_headers},
        )
        assert resp.status_code == 200

        # 5. Regular user cannot update ldap config
        resp = c.put(
            f"/api/v1/ldap_configs/{config_id}",
            json={"title": "Updated Title"},
            headers={"X-Project-ID": str(proj_id), **reg_headers},
        )
        assert resp.status_code == 403

        # 6. Regular user cannot delete ldap config
        resp = c.delete(
            f"/api/v1/ldap_configs/{config_id}",
            headers={
                "X-RESOURCE-NAME": "test-ldap-perm",
                "X-Project-ID": str(proj_id),
                **reg_headers,
            },
        )
        assert resp.status_code == 403

        # 7. Regular user cannot trigger test connection
        resp = c.post(
            "/api/v1/ldap_configs/_test-connection",
            json={"server_url": "ldap://ldap.example.com"},
            headers={"X-Project-ID": str(proj_id), **reg_headers},
        )
        assert resp.status_code == 403
        assert "Permission denied for 'ldap_config:test_connection'" in resp.text


def test_ldap_config_endpoints_with_granted_permissions(client: TestClient, test_project):
    """Verify users with granted service permissions can access allowed endpoints."""
    settings.enable_auth = True
    with client as c:
        admin_headers = _get_superadmin_headers(c)
        proj_id = test_project["id"]
        manager_headers = _create_and_login_user(c, admin_headers, "ldap_manager")
        reader_headers = _create_and_login_user(c, admin_headers, "ldap_reader")
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
                "/api/v1/ldap_configs",
                json={
                    "name": "mgr-ldap",
                    "title": "Mgr LDAP",
                    "server_url": "ldap://ldap.example.com",
                    "user_search_base": "ou=users,dc=example,dc=com",
                    "user_search_filter": "(uid={0})",
                    "username_attr": "uid",
                    "project_id": proj_id,
                },
                headers={"X-Project-ID": str(proj_id), **manager_headers},
            )
            assert resp.status_code == 200, resp.text
            created_id = resp.json()["data"]["id"]

            # Can update
            resp = c.put(
                f"/api/v1/ldap_configs/{created_id}",
                json={"title": "Updated Mgr LDAP"},
                headers={"X-Project-ID": str(proj_id), **manager_headers},
            )
            assert resp.status_code == 200

            # Can test connection
            with patch("ldap3.Server"), patch("ldap3.Connection") as mock_conn:
                mock_conn.return_value.bind.return_value = True
                resp = c.post(
                    "/api/v1/ldap_configs/_test-connection",
                    json={"server_url": "ldap://ldap.example.com", "storage_id": created_id},
                    headers={"X-Project-ID": str(proj_id), **manager_headers},
                )
                assert resp.status_code == 200
                assert resp.json()["status"] == "success"

            # Can delete
            resp = c.delete(
                f"/api/v1/ldap_configs/{created_id}",
                headers={
                    "X-RESOURCE-NAME": "mgr-ldap",
                    "X-Project-ID": str(proj_id),
                    **manager_headers,
                },
            )
            assert resp.status_code == 200

        # 2. User with Read permission (read-only control)
        # Create an ldap config as admin
        r_resp = c.post(
            "/api/v1/ldap_configs",
            json={
                "name": "view-ldap-target",
                "title": "View Target",
                "server_url": "ldap://ldap.example.com",
                "user_search_base": "ou=users,dc=example,dc=com",
                "user_search_filter": "(uid={0})",
                "username_attr": "uid",
                "project_id": proj_id,
            },
            headers={"X-Project-ID": str(proj_id), **admin_headers},
        )
        assert r_resp.status_code == 200
        target_id = r_resp.json()["data"]["id"]

        with patch("mindweaver.fw.permission.get_user_permissions", side_effect=_mock_perms([Read])):
            # Can list
            resp = c.get(
                "/api/v1/ldap_configs",
                headers={"X-Project-ID": str(proj_id), **reader_headers},
            )
            assert resp.status_code == 200

            # Can view
            resp = c.get(
                f"/api/v1/ldap_configs/{target_id}",
                headers={"X-Project-ID": str(proj_id), **reader_headers},
            )
            assert resp.status_code == 200

            # CANNOT create
            resp = c.post(
                "/api/v1/ldap_configs",
                json={
                    "name": "illegal-ldap-viewer",
                    "title": "Illegal",
                    "server_url": "ldap://ldap.example.com",
                    "user_search_base": "ou=users,dc=example,dc=com",
                    "user_search_filter": "(uid={0})",
                    "username_attr": "uid",
                    "project_id": proj_id,
                },
                headers={"X-Project-ID": str(proj_id), **reader_headers},
            )
            assert resp.status_code == 403

            # CANNOT update
            resp = c.put(
                f"/api/v1/ldap_configs/{target_id}",
                json={"title": "Updated by viewer"},
                headers={"X-Project-ID": str(proj_id), **reader_headers},
            )
            assert resp.status_code == 403

            # CANNOT test connection
            resp = c.post(
                "/api/v1/ldap_configs/_test-connection",
                json={"server_url": "ldap://ldap.example.com"},
                headers={"X-Project-ID": str(proj_id), **reader_headers},
            )
            assert resp.status_code == 403

            # CANNOT delete
            resp = c.delete(
                f"/api/v1/ldap_configs/{target_id}",
                headers={
                    "X-RESOURCE-NAME": "view-ldap-target",
                    "X-Project-ID": str(proj_id),
                    **reader_headers,
                },
            )
            assert resp.status_code == 403

        # 3. User with only TestConnection permission
        with patch("mindweaver.fw.permission.get_user_permissions", side_effect=_mock_perms([TestConnection])):
            # Tester cannot create
            resp = c.post(
                "/api/v1/ldap_configs",
                json={
                    "name": "illegal-ldap-tester",
                    "title": "Illegal",
                    "server_url": "ldap://ldap.example.com",
                    "user_search_base": "ou=users,dc=example,dc=com",
                    "user_search_filter": "(uid={0})",
                    "username_attr": "uid",
                    "project_id": proj_id,
                },
                headers={"X-Project-ID": str(proj_id), **tester_headers},
            )
            assert resp.status_code == 403

            # Tester CAN test connection
            with patch("ldap3.Server"), patch("ldap3.Connection") as mock_conn:
                mock_conn.return_value.bind.return_value = True
                resp = c.post(
                    "/api/v1/ldap_configs/_test-connection",
                    json={"server_url": "ldap://ldap.example.com", "storage_id": target_id},
                    headers={"X-Project-ID": str(proj_id), **tester_headers},
                )
                assert resp.status_code == 200
                assert resp.json()["status"] == "success"
