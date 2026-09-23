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
from mindweaver.service.project_user.permission import (
    Manage,
    Read,
    List,
    View,
    Write,
    Create,
    Update,
    Delete,
    Execute,
    ManageProjectUser,
    ManageProjectUserPermission,
    ProjectUser,
    ProjectUserPermission,
    ProjectUserRead,
    ProjectUserList,
    ProjectUserView,
    ProjectUserWrite,
    ProjectUserCreate,
    ProjectUserUpdate,
    ProjectUserDelete,
    ProjectUserExecute,
    ManageProjectLocalUser,
    ManageProjectLocalUserPermission,
    ProjectLocalUser,
    ProjectLocalUserPermission,
    ProjectLocalUserRead,
    ProjectLocalUserList,
    ProjectLocalUserView,
    ProjectLocalUserWrite,
    ProjectLocalUserCreate,
    ProjectLocalUserUpdate,
    ProjectLocalUserDelete,
    ProjectLocalUserExecute,
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


def test_project_user_permission_hierarchy():
    """Verify ProjectUser permission classes inherit correctly from All, Permission, and fw classes."""
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

    # Canonical Aliases (ProjectUser*)
    assert ManageProjectUser is Manage
    assert ManageProjectUserPermission is Manage
    assert ProjectUser is Manage
    assert ProjectUserPermission is Manage
    assert ProjectUserRead is Read
    assert ProjectUserList is List
    assert ProjectUserView is View
    assert ProjectUserWrite is Write
    assert ProjectUserCreate is Create
    assert ProjectUserUpdate is Update
    assert ProjectUserDelete is Delete
    assert ProjectUserExecute is Execute

    # Canonical Aliases (ProjectLocalUser*)
    assert ManageProjectLocalUser is Manage
    assert ManageProjectLocalUserPermission is Manage
    assert ProjectLocalUser is Manage
    assert ProjectLocalUserPermission is Manage
    assert ProjectLocalUserRead is Read
    assert ProjectLocalUserList is List
    assert ProjectLocalUserView is View
    assert ProjectLocalUserWrite is Write
    assert ProjectLocalUserCreate is Create
    assert ProjectLocalUserUpdate is Update
    assert ProjectLocalUserDelete is Delete
    assert ProjectLocalUserExecute is Execute


def test_project_user_permission_string_registration():
    """Verify that ProjectUser permission names are registered in _NAME_TO_PERMISSION via init_subclass."""
    assert _NAME_TO_PERMISSION.get("project_user:manage") is Manage
    assert _NAME_TO_PERMISSION.get("project_user:read") is Read
    assert _NAME_TO_PERMISSION.get("project_user:list") is List
    assert _NAME_TO_PERMISSION.get("project_user:view") is View
    assert _NAME_TO_PERMISSION.get("project_user:write") is Write
    assert _NAME_TO_PERMISSION.get("project_user:create") is Create
    assert _NAME_TO_PERMISSION.get("project_user:update") is Update
    assert _NAME_TO_PERMISSION.get("project_user:delete") is Delete
    assert _NAME_TO_PERMISSION.get("project_user:execute") is Execute
    # Verify manual aliases are not registered
    assert "project_user" not in _NAME_TO_PERMISSION
    assert "manage_project_user" not in _NAME_TO_PERMISSION


def test_project_user_check_user_permission_rules():
    """Verify check_user_permission evaluates service permissions accurately."""
    # 1. Superadmin has everything
    superadmin = DummyUser(is_superadmin=True)
    assert check_user_permission(superadmin, Manage)
    assert check_user_permission(superadmin, Read)
    assert check_user_permission(superadmin, List)
    assert check_user_permission(superadmin, Create)
    assert check_user_permission(superadmin, Update)
    assert check_user_permission(superadmin, Delete)
    assert check_user_permission(superadmin, Execute)

    # 2. User with Manage permission has all project user actions
    proj_user_admin = DummyUser(permissions=[Manage])
    assert check_user_permission(proj_user_admin, Manage)
    assert check_user_permission(proj_user_admin, Read)
    assert check_user_permission(proj_user_admin, List)
    assert check_user_permission(proj_user_admin, View)
    assert check_user_permission(proj_user_admin, Create)
    assert check_user_permission(proj_user_admin, Update)
    assert check_user_permission(proj_user_admin, Delete)
    assert check_user_permission(proj_user_admin, Execute)

    # 3. User with ProjectUserRead has List and View, but not mutating actions
    proj_user_reader = DummyUser(permissions=[Read])
    assert check_user_permission(proj_user_reader, Read)
    assert check_user_permission(proj_user_reader, List)
    assert check_user_permission(proj_user_reader, View)
    assert not check_user_permission(proj_user_reader, Manage)
    assert not check_user_permission(proj_user_reader, Write)
    assert not check_user_permission(proj_user_reader, Create)
    assert not check_user_permission(proj_user_reader, Update)
    assert not check_user_permission(proj_user_reader, Delete)
    assert not check_user_permission(proj_user_reader, Execute)

    # 4. User with Create can create but not list or delete
    creator = DummyUser(permissions=[Create])
    assert check_user_permission(creator, Create)
    assert not check_user_permission(creator, List)
    assert not check_user_permission(creator, Delete)
    assert not check_user_permission(creator, Update)

    # 5. Default authenticated user (with FwRead) can list and view project users
    default_user = DummyUser()
    assert check_user_permission(default_user, List)
    assert check_user_permission(default_user, View)
    assert not check_user_permission(default_user, Create)
    assert not check_user_permission(default_user, Update)
    assert not check_user_permission(default_user, Delete)


def test_project_user_endpoints_enforce_permissions(client: TestClient, test_project):
    """Verify project user endpoints enforce permissions via HTTP API."""
    settings.enable_auth = True
    with client as c:
        admin_headers = _get_superadmin_headers(c)
        reg_headers = _create_and_login_user(c, admin_headers, "regular_alice")
        proj_id = test_project["id"]

        user_payload = {
            "username": "alice-test-user",
            "email": "alice-test-user@example.com",
            "password": "supersecurepassword123",
            "password_confirm": "supersecurepassword123",
            "project_id": proj_id,
        }

        # 1. Regular user cannot create project local user
        resp = c.post(
            "/api/v1/project-local-users",
            json=user_payload,
            headers={"X-Project-ID": str(proj_id), **reg_headers},
        )
        assert resp.status_code == 403
        assert "Permission denied" in resp.text

        # 2. Superadmin can create project local user
        resp = c.post(
            "/api/v1/project-local-users",
            json=user_payload,
            headers={"X-Project-ID": str(proj_id), **admin_headers},
        )
        assert resp.status_code == 200, resp.text
        created_user = resp.json()["data"]
        user_id = created_user["id"]

        # 3. Regular user can view project local user
        resp = c.get(
            f"/api/v1/project-local-users/{user_id}",
            headers={"X-Project-ID": str(proj_id), **reg_headers},
        )
        assert resp.status_code == 200

        # 4. Regular user can list project local users
        resp = c.get(
            "/api/v1/project-local-users",
            headers={"X-Project-ID": str(proj_id), **reg_headers},
        )
        assert resp.status_code == 200

        # 5. Regular user cannot update project local user
        resp = c.put(
            f"/api/v1/project-local-users/{user_id}",
            json={
                "username": "alice-test-user-upd",
                "email": "alice-test-user-upd@example.com",
                "password": "__REDACTED__",
                "project_id": proj_id,
            },
            headers={"X-Project-ID": str(proj_id), **reg_headers},
        )
        assert resp.status_code == 403

        # 6. Regular user cannot delete project local user
        resp = c.delete(
            f"/api/v1/project-local-users/{user_id}",
            headers={
                "X-RESOURCE-NAME": "alice-test-user",
                "X-Project-ID": str(proj_id),
                **reg_headers,
            },
        )
        assert resp.status_code == 403


def test_project_user_endpoints_with_granted_permissions(client: TestClient, test_project):
    """Verify users with granted service permissions can access allowed endpoints."""
    settings.enable_auth = True
    with client as c:
        admin_headers = _get_superadmin_headers(c)
        proj_id = test_project["id"]
        manager_headers = _create_and_login_user(c, admin_headers, "proj_user_mgr")
        reader_headers = _create_and_login_user(c, admin_headers, "proj_user_reader")
        creator_headers = _create_and_login_user(c, admin_headers, "proj_user_creator")

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
                "/api/v1/project-local-users",
                json={
                    "username": "mgr-user",
                    "email": "mgr-user@example.com",
                    "password": "mgrpassword123",
                    "password_confirm": "mgrpassword123",
                    "project_id": proj_id,
                },
                headers={"X-Project-ID": str(proj_id), **manager_headers},
            )
            assert resp.status_code == 200, resp.text
            created_id = resp.json()["data"]["id"]

            # Can update
            resp = c.put(
                f"/api/v1/project-local-users/{created_id}",
                json={
                    "username": "mgr-user",
                    "email": "mgr-user-updated@example.com",
                    "password": "__REDACTED__",
                    "project_id": proj_id,
                },
                headers={"X-Project-ID": str(proj_id), **manager_headers},
            )
            assert resp.status_code == 200
            assert resp.json()["data"]["email"] == "mgr-user-updated@example.com"

            # Can delete
            resp = c.delete(
                f"/api/v1/project-local-users/{created_id}",
                headers={
                    "X-RESOURCE-NAME": "mgr-user",
                    "X-Project-ID": str(proj_id),
                    **manager_headers,
                },
            )
            assert resp.status_code == 200

        # 2. User with Read permission (read-only control)
        # Create a user as admin
        r_resp = c.post(
            "/api/v1/project-local-users",
            json={
                "username": "view-target-user",
                "email": "view-target-user@example.com",
                "password": "viewtargetpass123",
                "password_confirm": "viewtargetpass123",
                "project_id": proj_id,
            },
            headers={"X-Project-ID": str(proj_id), **admin_headers},
        )
        assert r_resp.status_code == 200
        target_id = r_resp.json()["data"]["id"]

        with patch("mindweaver.fw.permission.get_user_permissions", side_effect=_mock_perms([Read])):
            # Can list
            resp = c.get(
                "/api/v1/project-local-users",
                headers={"X-Project-ID": str(proj_id), **reader_headers},
            )
            assert resp.status_code == 200

            # Can view
            resp = c.get(
                f"/api/v1/project-local-users/{target_id}",
                headers={"X-Project-ID": str(proj_id), **reader_headers},
            )
            assert resp.status_code == 200

            # CANNOT create
            resp = c.post(
                "/api/v1/project-local-users",
                json={
                    "username": "illegal-viewer-user",
                    "email": "illegal-viewer-user@example.com",
                    "password": "viewerpass123",
                    "password_confirm": "viewerpass123",
                    "project_id": proj_id,
                },
                headers={"X-Project-ID": str(proj_id), **reader_headers},
            )
            assert resp.status_code == 403

            # CANNOT update
            resp = c.put(
                f"/api/v1/project-local-users/{target_id}",
                json={
                    "username": "view-target-user",
                    "email": "view-target-user-upd@example.com",
                    "password": "__REDACTED__",
                    "project_id": proj_id,
                },
                headers={"X-Project-ID": str(proj_id), **reader_headers},
            )
            assert resp.status_code == 403

            # CANNOT delete
            resp = c.delete(
                f"/api/v1/project-local-users/{target_id}",
                headers={
                    "X-RESOURCE-NAME": "view-target-user",
                    "X-Project-ID": str(proj_id),
                    **reader_headers,
                },
            )
            assert resp.status_code == 403

        # 3. User with only Create permission
        with patch("mindweaver.fw.permission.get_user_permissions", side_effect=_mock_perms([Create])):
            # Creator can create
            resp = c.post(
                "/api/v1/project-local-users",
                json={
                    "username": "creator-made-user",
                    "email": "creator-made-user@example.com",
                    "password": "creatorpass123",
                    "password_confirm": "creatorpass123",
                    "project_id": proj_id,
                },
                headers={"X-Project-ID": str(proj_id), **creator_headers},
            )
            assert resp.status_code == 200
            new_id = resp.json()["data"]["id"]

            # Creator CANNOT update
            resp = c.put(
                f"/api/v1/project-local-users/{new_id}",
                json={
                    "username": "creator-made-user",
                    "email": "creator-made-user-upd@example.com",
                    "password": "__REDACTED__",
                    "project_id": proj_id,
                },
                headers={"X-Project-ID": str(proj_id), **creator_headers},
            )
            assert resp.status_code == 403

            # Creator CANNOT delete
            resp = c.delete(
                f"/api/v1/project-local-users/{new_id}",
                headers={
                    "X-RESOURCE-NAME": "creator-made-user",
                    "X-Project-ID": str(proj_id),
                    **creator_headers,
                },
            )
            assert resp.status_code == 403
