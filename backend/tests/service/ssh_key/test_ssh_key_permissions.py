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
from mindweaver.service.ssh_key.permission import (
    Manage,
    Read,
    List,
    View,
    Write,
    Create,
    Update,
    Delete,
    Execute,
    ManageSSHKey,
    ManageSSHKeyPermission,
    SSHKey,
    SSHKeyPermission,
    SSHKeyRead,
    SSHKeyList,
    SSHKeyView,
    SSHKeyWrite,
    SSHKeyCreate,
    SSHKeyUpdate,
    SSHKeyDelete,
    SSHKeyExecute,
    ManageSshKey,
    ManageSshKeyPermission,
    SshKey,
    SshKeyPermission,
    SshKeyRead,
    SshKeyList,
    SshKeyView,
    SshKeyWrite,
    SshKeyCreate,
    SshKeyUpdate,
    SshKeyDelete,
    SshKeyExecute,
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


def test_ssh_key_permission_hierarchy():
    """Verify SSHKey permission classes inherit correctly from All, Permission, and fw classes."""
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

    # Canonical Aliases (SSHKey*)
    assert ManageSSHKey is Manage
    assert ManageSSHKeyPermission is Manage
    assert SSHKey is Manage
    assert SSHKeyPermission is Manage
    assert SSHKeyRead is Read
    assert SSHKeyList is List
    assert SSHKeyView is View
    assert SSHKeyWrite is Write
    assert SSHKeyCreate is Create
    assert SSHKeyUpdate is Update
    assert SSHKeyDelete is Delete
    assert SSHKeyExecute is Execute

    # Canonical Aliases (SshKey*)
    assert ManageSshKey is Manage
    assert ManageSshKeyPermission is Manage
    assert SshKey is Manage
    assert SshKeyPermission is Manage
    assert SshKeyRead is Read
    assert SshKeyList is List
    assert SshKeyView is View
    assert SshKeyWrite is Write
    assert SshKeyCreate is Create
    assert SshKeyUpdate is Update
    assert SshKeyDelete is Delete
    assert SshKeyExecute is Execute


def test_ssh_key_permission_string_registration():
    """Verify that SSHKey permission names are registered in _NAME_TO_PERMISSION via init_subclass."""
    assert _NAME_TO_PERMISSION.get("ssh_key:manage") is Manage
    assert _NAME_TO_PERMISSION.get("ssh_key:read") is Read
    assert _NAME_TO_PERMISSION.get("ssh_key:list") is List
    assert _NAME_TO_PERMISSION.get("ssh_key:view") is View
    assert _NAME_TO_PERMISSION.get("ssh_key:write") is Write
    assert _NAME_TO_PERMISSION.get("ssh_key:create") is Create
    assert _NAME_TO_PERMISSION.get("ssh_key:update") is Update
    assert _NAME_TO_PERMISSION.get("ssh_key:delete") is Delete
    assert _NAME_TO_PERMISSION.get("ssh_key:execute") is Execute
    assert "ssh_key" not in _NAME_TO_PERMISSION
    assert "manage_ssh_key" not in _NAME_TO_PERMISSION


def test_ssh_key_check_user_permission_rules():
    """Verify check_user_permission evaluates service permissions accurately."""
    # 1. Superadmin has everything
    superadmin = DummyUser(is_superadmin=True)
    assert check_user_permission(superadmin, Manage)
    assert check_user_permission(superadmin, Read)
    assert check_user_permission(superadmin, List)
    assert check_user_permission(superadmin, Create)
    assert check_user_permission(superadmin, Delete)

    # 2. User with Manage permission has all ssh key actions
    key_admin = DummyUser(permissions=[Manage])
    assert check_user_permission(key_admin, Manage)
    assert check_user_permission(key_admin, Read)
    assert check_user_permission(key_admin, List)
    assert check_user_permission(key_admin, View)
    assert check_user_permission(key_admin, Create)
    assert check_user_permission(key_admin, Update)
    assert check_user_permission(key_admin, Delete)

    # 3. User with Read has List and View, but not mutating or execute actions
    key_reader = DummyUser(permissions=[Read])
    assert check_user_permission(key_reader, Read)
    assert check_user_permission(key_reader, List)
    assert check_user_permission(key_reader, View)
    assert not check_user_permission(key_reader, Manage)
    assert not check_user_permission(key_reader, Write)
    assert not check_user_permission(key_reader, Create)
    assert not check_user_permission(key_reader, Update)
    assert not check_user_permission(key_reader, Delete)
    assert not check_user_permission(key_reader, Execute)

    # 4. User with Create can create but not update or delete
    key_creator = DummyUser(permissions=[Create])
    assert check_user_permission(key_creator, Create)
    assert not check_user_permission(key_creator, Write)
    assert not check_user_permission(key_creator, Manage)
    assert not check_user_permission(key_creator, Read)
    assert not check_user_permission(key_creator, List)
    assert not check_user_permission(key_creator, View)
    assert not check_user_permission(key_creator, Update)
    assert not check_user_permission(key_creator, Delete)

    # 5. Default authenticated user (with FwRead) can list and view ssh keys
    default_user = DummyUser()
    assert check_user_permission(default_user, List)
    assert check_user_permission(default_user, View)
    assert not check_user_permission(default_user, Create)
    assert not check_user_permission(default_user, Update)
    assert not check_user_permission(default_user, Delete)


def test_ssh_key_endpoints_enforce_permissions(client: TestClient, test_project):
    """Verify ssh key endpoints enforce permissions via HTTP API."""
    settings.enable_auth = True
    with client as c:
        admin_headers = _get_superadmin_headers(c)
        reg_headers = _create_and_login_user(c, admin_headers, "regular_alice")
        proj_id = test_project["id"]

        # 1. Regular user cannot create ssh key
        resp = c.post(
            "/api/v1/ssh_keys",
            json={
                "name": "perm-key",
                "title": "Perm Key",
                "algorithm": "ed25519",
                "project_id": proj_id,
            },
            headers={"X-Project-ID": str(proj_id), **reg_headers},
        )
        assert resp.status_code == 403
        assert "Permission denied" in resp.text

        # 2. Superadmin can create ssh key
        resp = c.post(
            "/api/v1/ssh_keys",
            json={
                "name": "perm-key",
                "title": "Perm Key",
                "algorithm": "ed25519",
                "project_id": proj_id,
            },
            headers={"X-Project-ID": str(proj_id), **admin_headers},
        )
        assert resp.status_code == 200, resp.text
        key_id = resp.json()["data"]["id"]

        # 3. Regular user can view ssh key
        resp = c.get(
            f"/api/v1/ssh_keys/{key_id}",
            headers={"X-Project-ID": str(proj_id), **reg_headers},
        )
        assert resp.status_code == 200

        # 4. Regular user can list ssh keys
        resp = c.get(
            "/api/v1/ssh_keys",
            headers={"X-Project-ID": str(proj_id), **reg_headers},
        )
        assert resp.status_code == 200

        # 5. Regular user cannot update ssh key
        resp = c.put(
            f"/api/v1/ssh_keys/{key_id}",
            json={"title": "Updated Title"},
            headers={"X-Project-ID": str(proj_id), **reg_headers},
        )
        assert resp.status_code == 403

        # 6. Regular user cannot delete ssh key
        resp = c.delete(
            f"/api/v1/ssh_keys/{key_id}",
            headers={
                "X-RESOURCE-NAME": "perm-key",
                "X-Project-ID": str(proj_id),
                **reg_headers,
            },
        )
        assert resp.status_code == 403


def test_ssh_key_endpoints_with_granted_permissions(client: TestClient, test_project):
    """Verify users with granted service permissions can access allowed endpoints."""
    settings.enable_auth = True
    with client as c:
        admin_headers = _get_superadmin_headers(c)
        proj_id = test_project["id"]
        manager_headers = _create_and_login_user(c, admin_headers, "key_manager")
        reader_headers = _create_and_login_user(c, admin_headers, "key_reader")
        creator_headers = _create_and_login_user(c, admin_headers, "key_creator")

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
                "/api/v1/ssh_keys",
                json={
                    "name": "mgr-key",
                    "title": "Mgr SSH Key",
                    "algorithm": "rsa",
                    "key_size": 2048,
                    "project_id": proj_id,
                },
                headers={"X-Project-ID": str(proj_id), **manager_headers},
            )
            assert resp.status_code == 200, resp.text
            created_id = resp.json()["data"]["id"]

            # Can update
            resp = c.put(
                f"/api/v1/ssh_keys/{created_id}",
                json={"title": "Updated Mgr SSH Key"},
                headers={"X-Project-ID": str(proj_id), **manager_headers},
            )
            assert resp.status_code == 200

            # Can delete
            resp = c.delete(
                f"/api/v1/ssh_keys/{created_id}",
                headers={
                    "X-RESOURCE-NAME": "mgr-key",
                    "X-Project-ID": str(proj_id),
                    **manager_headers,
                },
            )
            assert resp.status_code == 200

        # 2. User with Read permission (read-only control)
        # Create an SSH key as admin
        r_resp = c.post(
            "/api/v1/ssh_keys",
            json={
                "name": "view-key-target",
                "title": "View Target",
                "algorithm": "ed25519",
                "project_id": proj_id,
            },
            headers={"X-Project-ID": str(proj_id), **admin_headers},
        )
        assert r_resp.status_code == 200
        target_key_id = r_resp.json()["data"]["id"]

        with patch("mindweaver.fw.permission.get_user_permissions", side_effect=_mock_perms([Read])):
            # Can list
            resp = c.get(
                "/api/v1/ssh_keys",
                headers={"X-Project-ID": str(proj_id), **reader_headers},
            )
            assert resp.status_code == 200

            # Can view
            resp = c.get(
                f"/api/v1/ssh_keys/{target_key_id}",
                headers={"X-Project-ID": str(proj_id), **reader_headers},
            )
            assert resp.status_code == 200

            # CANNOT create
            resp = c.post(
                "/api/v1/ssh_keys",
                json={
                    "name": "illegal-key-viewer",
                    "title": "Illegal",
                    "algorithm": "ed25519",
                    "project_id": proj_id,
                },
                headers={"X-Project-ID": str(proj_id), **reader_headers},
            )
            assert resp.status_code == 403

            # CANNOT update
            resp = c.put(
                f"/api/v1/ssh_keys/{target_key_id}",
                json={"title": "Updated by viewer"},
                headers={"X-Project-ID": str(proj_id), **reader_headers},
            )
            assert resp.status_code == 403

            # CANNOT delete
            resp = c.delete(
                f"/api/v1/ssh_keys/{target_key_id}",
                headers={
                    "X-RESOURCE-NAME": "view-key-target",
                    "X-Project-ID": str(proj_id),
                    **reader_headers,
                },
            )
            assert resp.status_code == 403

        # 3. User with only Create permission
        with patch("mindweaver.fw.permission.get_user_permissions", side_effect=_mock_perms([Create])):
            # Creator can create
            resp = c.post(
                "/api/v1/ssh_keys",
                json={
                    "name": "creator-key",
                    "title": "Creator Key",
                    "algorithm": "ed25519",
                    "project_id": proj_id,
                },
                headers={"X-Project-ID": str(proj_id), **creator_headers},
            )
            assert resp.status_code == 200
            new_id = resp.json()["data"]["id"]

            # Creator CANNOT update
            resp = c.put(
                f"/api/v1/ssh_keys/{new_id}",
                json={"title": "Updated by creator"},
                headers={"X-Project-ID": str(proj_id), **creator_headers},
            )
            assert resp.status_code == 403

            # Creator CANNOT delete
            resp = c.delete(
                f"/api/v1/ssh_keys/{new_id}",
                headers={
                    "X-RESOURCE-NAME": "creator-key",
                    "X-Project-ID": str(proj_id),
                    **creator_headers,
                },
            )
            assert resp.status_code == 403
