# SPDX-FileCopyrightText: Copyright © 2026 Mohd Izhar Firdaus Bin Ismail
# SPDX-License-Identifier: AGPLv3+

import pytest
from unittest.mock import patch
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
from mindweaver.fw.auth.permission import (
    Manage,
    Read,
    List,
    View,
    Write,
    Create,
    Update,
    Delete,
    Execute,
    Me,
    UpdateMe,
    ManageAuth,
    ManageAuthPermission,
    Auth,
    AuthPermission,
    AuthRead,
    AuthList,
    AuthView,
    AuthWrite,
    AuthCreate,
    AuthUpdate,
    AuthDelete,
    AuthExecute,
    AuthMe,
    AuthUpdateMe,
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
    c: TestClient, admin_headers: dict, username: str
) -> dict:
    """Create a user and return auth headers."""
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


def test_auth_permission_hierarchy():
    """Verify Auth permission classes inherit correctly from All, Permission, and fw classes."""
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
    assert issubclass(Me, View)
    assert issubclass(Me, Read)
    assert issubclass(Me, Manage)
    assert issubclass(Me, FwView)

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
    assert issubclass(UpdateMe, Update)
    assert issubclass(UpdateMe, FwRead)

    # Execute hierarchy (inherits from Manage)
    assert issubclass(Execute, Manage)
    assert not issubclass(Execute, Read)
    assert issubclass(Execute, FwExecute)

    # Canonical Aliases (Auth*)
    assert ManageAuth is Manage
    assert ManageAuthPermission is Manage
    assert Auth is Manage
    assert AuthPermission is Manage
    assert AuthRead is Read
    assert AuthList is List
    assert AuthView is View
    assert AuthWrite is Write
    assert AuthCreate is Create
    assert AuthUpdate is Update
    assert AuthDelete is Delete
    assert AuthExecute is Execute
    assert AuthMe is Me
    assert AuthUpdateMe is UpdateMe


def test_auth_permission_string_registration():
    """Verify that Auth permission names are registered in _NAME_TO_PERMISSION via init_subclass."""
    assert _NAME_TO_PERMISSION.get("auth:manage") is Manage
    assert _NAME_TO_PERMISSION.get("auth:read") is Read
    assert _NAME_TO_PERMISSION.get("auth:list") is List
    assert _NAME_TO_PERMISSION.get("auth:view") is View
    assert _NAME_TO_PERMISSION.get("auth:write") is Write
    assert _NAME_TO_PERMISSION.get("auth:create") is Create
    assert _NAME_TO_PERMISSION.get("auth:update") is Update
    assert _NAME_TO_PERMISSION.get("auth:delete") is Delete
    assert _NAME_TO_PERMISSION.get("auth:execute") is Execute
    assert _NAME_TO_PERMISSION.get("auth:me") is Me
    assert _NAME_TO_PERMISSION.get("auth:updateme") is UpdateMe
    assert "auth" not in _NAME_TO_PERMISSION


def test_auth_check_user_permission_rules():
    """Verify check_user_permission evaluates auth permissions accurately."""
    # 1. Superadmin has everything
    superadmin = DummyUser(is_superadmin=True)
    assert check_user_permission(superadmin, Manage)
    assert check_user_permission(superadmin, Read)
    assert check_user_permission(superadmin, List)
    assert check_user_permission(superadmin, View)
    assert check_user_permission(superadmin, Me)
    assert check_user_permission(superadmin, UpdateMe)
    assert check_user_permission(superadmin, Create)
    assert check_user_permission(superadmin, Delete)

    # 2. User with Manage permission has all auth actions
    auth_admin = DummyUser(permissions=[Manage])
    assert check_user_permission(auth_admin, Manage)
    assert check_user_permission(auth_admin, Read)
    assert check_user_permission(auth_admin, List)
    assert check_user_permission(auth_admin, View)
    assert check_user_permission(auth_admin, Me)
    assert check_user_permission(auth_admin, UpdateMe)
    assert check_user_permission(auth_admin, Create)
    assert check_user_permission(auth_admin, Update)
    assert check_user_permission(auth_admin, Delete)
    assert check_user_permission(auth_admin, Execute)

    # 3. User with Read has List, View, Me, and UpdateMe (since UpdateMe inherits FwRead)
    auth_reader = DummyUser(permissions=[Read])
    assert check_user_permission(auth_reader, Read)
    assert check_user_permission(auth_reader, List)
    assert check_user_permission(auth_reader, View)
    assert check_user_permission(auth_reader, Me)
    assert check_user_permission(auth_reader, UpdateMe)
    assert not check_user_permission(auth_reader, Manage)
    assert not check_user_permission(auth_reader, Write)
    assert not check_user_permission(auth_reader, Create)
    assert not check_user_permission(auth_reader, Delete)
    assert not check_user_permission(auth_reader, Execute)

    # 4. User with Create can create but not read or delete
    auth_creator = DummyUser(permissions=[Create])
    assert check_user_permission(auth_creator, Create)
    assert not check_user_permission(auth_creator, Write)
    assert not check_user_permission(auth_creator, Manage)
    assert not check_user_permission(auth_creator, Read)
    assert not check_user_permission(auth_creator, List)
    assert not check_user_permission(auth_creator, View)
    assert not check_user_permission(auth_creator, Me)
    assert not check_user_permission(auth_creator, Update)
    assert not check_user_permission(auth_creator, Delete)

    # 5. Default authenticated user (with FwRead) can read profile and update own profile
    default_user = DummyUser()
    assert check_user_permission(default_user, List)
    assert check_user_permission(default_user, View)
    assert check_user_permission(default_user, Me)
    assert check_user_permission(default_user, UpdateMe)
    assert not check_user_permission(default_user, Create)
    assert not check_user_permission(default_user, Delete)


def test_auth_endpoints_enforce_permissions(client: TestClient):
    """Verify auth endpoints enforce permissions via HTTP API."""
    settings.enable_auth = True
    with client as c:
        admin_headers = _get_superadmin_headers(c)
        reg_headers = _create_and_login_user(c, admin_headers, "auth_perm_user")

        # 1. Regular user can get /me
        resp = c.get("/api/v1/auth/me", headers=reg_headers)
        assert resp.status_code == 200
        assert resp.json()["name"] == "auth_perm_user"

        # 2. Regular user can update /me
        resp = c.put(
            "/api/v1/auth/me",
            json={"display_name": "Auth Perm Updated"},
            headers=reg_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["display_name"] == "Auth Perm Updated"

        # 3. Superadmin can get /me
        resp = c.get("/api/v1/auth/me", headers=admin_headers)
        assert resp.status_code == 200
        assert resp.json()["name"] == "admin"


def test_auth_endpoints_with_custom_permissions(client: TestClient):
    """Verify users with specific permissions access /me appropriately."""
    settings.enable_auth = True
    with client as c:
        admin_headers = _get_superadmin_headers(c)
        user_headers = _create_and_login_user(c, admin_headers, "restricted_auth_user")

        def _mock_perms(custom_perms):
            def _get(u, *args, **kwargs):
                if getattr(u, "is_superadmin", False):
                    return [All]
                return custom_perms
            return _get

        # User with only Create permission cannot view /me or update /me
        with patch("mindweaver.fw.permission.get_user_permissions", side_effect=_mock_perms([Create])):
            resp = c.get("/api/v1/auth/me", headers=user_headers)
            assert resp.status_code == 403
            assert "Permission denied" in resp.text

            resp = c.put(
                "/api/v1/auth/me",
                json={"display_name": "Should Fail"},
                headers=user_headers,
            )
            assert resp.status_code == 403
            assert "Permission denied" in resp.text

        # User with Manage can access /me (GET and PUT)
        with patch("mindweaver.fw.permission.get_user_permissions", side_effect=_mock_perms([Manage])):
            resp = c.get("/api/v1/auth/me", headers=user_headers)
            assert resp.status_code == 200

            resp = c.put(
                "/api/v1/auth/me",
                json={"display_name": "Manager Updated"},
                headers=user_headers,
            )
            assert resp.status_code == 200
            assert resp.json()["display_name"] == "Manager Updated"
