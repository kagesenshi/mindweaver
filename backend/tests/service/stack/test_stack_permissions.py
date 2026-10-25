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
from mindweaver.service.stack.permission import (
    Manage,
    Read,
    List,
    View,
    Write,
    Create,
    Update,
    Delete,
    Execute,
    ManageStack,
    ManageStackPermission,
    Stack,
    StackPermission,
    StackRead,
    StackList,
    StackView,
    StackWrite,
    StackCreate,
    StackUpdate,
    StackDelete,
    StackExecute,
    ManageStacks,
    ManageStacksPermission,
    Stacks,
    StacksPermission,
    StacksRead,
    StacksList,
    StacksView,
    StacksWrite,
    StacksCreate,
    StacksUpdate,
    StacksDelete,
    StacksExecute,
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


def test_stack_permission_hierarchy():
    """Verify Stack permission classes inherit correctly from All, Permission, and fw classes."""
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

    # Canonical Aliases (Stack*)
    assert ManageStack is Manage
    assert ManageStackPermission is Manage
    assert Stack is Manage
    assert StackPermission is Manage
    assert StackRead is Read
    assert StackList is List
    assert StackView is View
    assert StackWrite is Write
    assert StackCreate is Create
    assert StackUpdate is Update
    assert StackDelete is Delete
    assert StackExecute is Execute

    # Canonical Aliases (Stacks*)
    assert ManageStacks is Manage
    assert ManageStacksPermission is Manage
    assert Stacks is Manage
    assert StacksPermission is Manage
    assert StacksRead is Read
    assert StacksList is List
    assert StacksView is View
    assert StacksWrite is Write
    assert StacksCreate is Create
    assert StacksUpdate is Update
    assert StacksDelete is Delete
    assert StacksExecute is Execute


def test_stack_permission_string_registration():
    """Verify that Stack permission names are registered in _NAME_TO_PERMISSION via init_subclass."""
    assert _NAME_TO_PERMISSION.get("stack:manage") is Manage
    assert _NAME_TO_PERMISSION.get("stack:read") is Read
    assert _NAME_TO_PERMISSION.get("stack:list") is List
    assert _NAME_TO_PERMISSION.get("stack:view") is View
    assert _NAME_TO_PERMISSION.get("stack:write") is Write
    assert _NAME_TO_PERMISSION.get("stack:create") is Create
    assert _NAME_TO_PERMISSION.get("stack:update") is Update
    assert _NAME_TO_PERMISSION.get("stack:delete") is Delete
    assert _NAME_TO_PERMISSION.get("stack:execute") is Execute
    assert "stack" not in _NAME_TO_PERMISSION
    assert "manage_stack" not in _NAME_TO_PERMISSION


def test_stack_check_user_permission_rules():
    """Verify check_user_permission evaluates service permissions accurately."""
    # 1. Superadmin has everything
    superadmin = DummyUser(is_superadmin=True)
    assert check_user_permission(superadmin, Manage)
    assert check_user_permission(superadmin, Read)
    assert check_user_permission(superadmin, List)
    assert check_user_permission(superadmin, Create)
    assert check_user_permission(superadmin, Delete)

    # 2. User with Manage permission has all stack actions
    stack_admin = DummyUser(permissions=[Manage])
    assert check_user_permission(stack_admin, Manage)
    assert check_user_permission(stack_admin, Read)
    assert check_user_permission(stack_admin, List)
    assert check_user_permission(stack_admin, View)
    assert check_user_permission(stack_admin, Create)
    assert check_user_permission(stack_admin, Update)
    assert check_user_permission(stack_admin, Delete)
    assert check_user_permission(stack_admin, Execute)

    # 3. User with Read has List and View, but not mutating or execute actions
    stack_reader = DummyUser(permissions=[Read])
    assert check_user_permission(stack_reader, Read)
    assert check_user_permission(stack_reader, List)
    assert check_user_permission(stack_reader, View)
    assert not check_user_permission(stack_reader, Manage)
    assert not check_user_permission(stack_reader, Write)
    assert not check_user_permission(stack_reader, Create)
    assert not check_user_permission(stack_reader, Update)
    assert not check_user_permission(stack_reader, Delete)
    assert not check_user_permission(stack_reader, Execute)

    # 4. User with Create can create but not update or delete
    stack_creator = DummyUser(permissions=[Create])
    assert check_user_permission(stack_creator, Create)
    assert not check_user_permission(stack_creator, Write)
    assert not check_user_permission(stack_creator, Manage)
    assert not check_user_permission(stack_creator, Read)
    assert not check_user_permission(stack_creator, List)
    assert not check_user_permission(stack_creator, View)
    assert not check_user_permission(stack_creator, Update)
    assert not check_user_permission(stack_creator, Delete)

    # 5. Default authenticated user (with FwRead) can list and view stacks
    default_user = DummyUser()
    assert check_user_permission(default_user, List)
    assert check_user_permission(default_user, View)
    assert not check_user_permission(default_user, Create)
    assert not check_user_permission(default_user, Update)
    assert not check_user_permission(default_user, Delete)


def test_stack_endpoints_enforce_permissions(client: TestClient):
    """Verify stack endpoints enforce permissions via HTTP API."""
    settings.enable_auth = True
    with client as c:
        admin_headers = _get_superadmin_headers(c)
        reg_headers = _create_and_login_user(c, admin_headers, "regular_stack_user")

        # 1. Regular user cannot create stack
        resp = c.post(
            "/api/v1/stacks",
            json={
                "name": "perm-stack",
                "title": "Perm Stack",
                "version": "1.0.0",
                "configuration": {"components": {}},
            },
            headers=reg_headers,
        )
        assert resp.status_code == 403
        assert "Permission denied" in resp.text

        # 2. Superadmin can create stack
        resp = c.post(
            "/api/v1/stacks",
            json={
                "name": "perm-stack",
                "title": "Perm Stack",
                "version": "1.0.0",
                "configuration": {"components": {}},
            },
            headers=admin_headers,
        )
        assert resp.status_code == 200, resp.text
        stack_id = resp.json()["data"]["id"]

        # 3. Regular user can view stack
        resp = c.get(
            f"/api/v1/stacks/{stack_id}",
            headers=reg_headers,
        )
        assert resp.status_code == 200

        # 4. Regular user can list stacks
        resp = c.get(
            "/api/v1/stacks",
            headers=reg_headers,
        )
        assert resp.status_code == 200

        # 5. Regular user cannot update stack
        resp = c.put(
            f"/api/v1/stacks/{stack_id}",
            json={"title": "Updated Title"},
            headers=reg_headers,
        )
        assert resp.status_code == 403

        # 6. Regular user cannot delete stack
        resp = c.delete(
            f"/api/v1/stacks/{stack_id}",
            headers={
                "X-RESOURCE-NAME": "perm-stack",
                **reg_headers,
            },
        )
        assert resp.status_code == 403


def test_stack_endpoints_with_granted_permissions(client: TestClient):
    """Verify users with granted service permissions can access allowed endpoints."""
    settings.enable_auth = True
    with client as c:
        admin_headers = _get_superadmin_headers(c)
        manager_headers = _create_and_login_user(c, admin_headers, "stack_manager")
        reader_headers = _create_and_login_user(c, admin_headers, "stack_reader")
        creator_headers = _create_and_login_user(c, admin_headers, "stack_creator")

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
                "/api/v1/stacks",
                json={
                    "name": "mgr-stack",
                    "title": "Mgr Stack",
                    "version": "1.0.1",
                    "configuration": {"components": {}},
                },
                headers=manager_headers,
            )
            assert resp.status_code == 200, resp.text
            created_id = resp.json()["data"]["id"]

            # Can update
            resp = c.put(
                f"/api/v1/stacks/{created_id}",
                json={"title": "Updated Mgr Stack"},
                headers=manager_headers,
            )
            assert resp.status_code == 200

            # Can delete
            resp = c.delete(
                f"/api/v1/stacks/{created_id}",
                headers={
                    "X-RESOURCE-NAME": "mgr-stack",
                    **manager_headers,
                },
            )
            assert resp.status_code == 200

        # 2. User with Read permission (read-only control)
        r_resp = c.post(
            "/api/v1/stacks",
            json={
                "name": "view-stack-target",
                "title": "View Target",
                "version": "1.0.2",
                "configuration": {"components": {}},
            },
            headers=admin_headers,
        )
        assert r_resp.status_code == 200
        target_stack_id = r_resp.json()["data"]["id"]

        with patch("mindweaver.fw.permission.get_user_permissions", side_effect=_mock_perms([Read])):
            # Can list
            resp = c.get(
                "/api/v1/stacks",
                headers=reader_headers,
            )
            assert resp.status_code == 200

            # Can view
            resp = c.get(
                f"/api/v1/stacks/{target_stack_id}",
                headers=reader_headers,
            )
            assert resp.status_code == 200

            # CANNOT create
            resp = c.post(
                "/api/v1/stacks",
                json={
                    "name": "illegal-stack-viewer",
                    "title": "Illegal",
                    "version": "1.0.3",
                    "configuration": {"components": {}},
                },
                headers=reader_headers,
            )
            assert resp.status_code == 403

            # CANNOT update
            resp = c.put(
                f"/api/v1/stacks/{target_stack_id}",
                json={"title": "Updated by viewer"},
                headers=reader_headers,
            )
            assert resp.status_code == 403

            # CANNOT delete
            resp = c.delete(
                f"/api/v1/stacks/{target_stack_id}",
                headers={
                    "X-RESOURCE-NAME": "view-stack-target",
                    **reader_headers,
                },
            )
            assert resp.status_code == 403

        # 3. User with only Create permission
        with patch("mindweaver.fw.permission.get_user_permissions", side_effect=_mock_perms([Create])):
            # Creator can create
            resp = c.post(
                "/api/v1/stacks",
                json={
                    "name": "creator-stack",
                    "title": "Creator Stack",
                    "version": "1.0.4",
                    "configuration": {"components": {}},
                },
                headers=creator_headers,
            )
            assert resp.status_code == 200
            new_id = resp.json()["data"]["id"]

            # Creator CANNOT update
            resp = c.put(
                f"/api/v1/stacks/{new_id}",
                json={"title": "Updated by creator"},
                headers=creator_headers,
            )
            assert resp.status_code == 403

            # Creator CANNOT delete
            resp = c.delete(
                f"/api/v1/stacks/{new_id}",
                headers={
                    "X-RESOURCE-NAME": "creator-stack",
                    **creator_headers,
                },
            )
            assert resp.status_code == 403
