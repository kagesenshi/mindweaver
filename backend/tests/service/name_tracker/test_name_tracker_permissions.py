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
from mindweaver.service.name_tracker.permission import (
    Manage,
    NameTracker,
    Read,
    List,
    View,
    Write,
    Create,
    Update,
    Delete,
    Execute,
    CheckAvailability,
    ManageNameTrackerPermission,
    ManageNameTracker,
    NameTrackerPermission,
    NameTrackerRead,
    NameTrackerList,
    NameTrackerView,
    NameTrackerWrite,
    NameTrackerCreate,
    NameTrackerUpdate,
    NameTrackerDelete,
    NameTrackerExecute,
    NameTrackerCheckAvailability,
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


def test_name_tracker_permission_hierarchy():
    """Verify NameTracker permission classes inherit correctly from All, Permission, and fw classes."""
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

    # CheckAvailability hierarchy (inherits from View)
    assert issubclass(CheckAvailability, View)
    assert issubclass(CheckAvailability, Read)
    assert issubclass(CheckAvailability, Manage)
    assert issubclass(CheckAvailability, FwRead)
    assert issubclass(CheckAvailability, FwView)

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

    # Aliases
    assert ManageNameTracker is Manage
    assert ManageNameTrackerPermission is Manage
    assert NameTracker is Manage
    assert NameTrackerPermission is Manage
    assert NameTrackerRead is Read
    assert NameTrackerList is List
    assert NameTrackerView is View
    assert NameTrackerWrite is Write
    assert NameTrackerCreate is Create
    assert NameTrackerUpdate is Update
    assert NameTrackerDelete is Delete
    assert NameTrackerExecute is Execute
    assert NameTrackerCheckAvailability is CheckAvailability


def test_name_tracker_permission_string_registration():
    """Verify that NameTracker permission names are registered in _NAME_TO_PERMISSION via init_subclass."""
    assert _NAME_TO_PERMISSION.get("name_tracker:manage") is Manage
    assert _NAME_TO_PERMISSION.get("name_tracker:read") is Read
    assert _NAME_TO_PERMISSION.get("name_tracker:list") is List
    assert _NAME_TO_PERMISSION.get("name_tracker:view") is View
    assert _NAME_TO_PERMISSION.get("name_tracker:write") is Write
    assert _NAME_TO_PERMISSION.get("name_tracker:create") is Create
    assert _NAME_TO_PERMISSION.get("name_tracker:update") is Update
    assert _NAME_TO_PERMISSION.get("name_tracker:delete") is Delete
    assert _NAME_TO_PERMISSION.get("name_tracker:execute") is Execute
    assert _NAME_TO_PERMISSION.get("name_tracker:check_availability") is CheckAvailability
    # Verify removed view_name_tracker is not registered
    assert "name_tracker:view_name_tracker" not in _NAME_TO_PERMISSION
    assert "name_tracker" not in _NAME_TO_PERMISSION
    assert "manage_name_tracker" not in _NAME_TO_PERMISSION


def test_name_tracker_check_user_permission_rules():
    """Verify check_user_permission evaluates service permissions accurately."""
    # 1. Superadmin has everything
    superadmin = DummyUser(is_superadmin=True)
    assert check_user_permission(superadmin, Manage)
    assert check_user_permission(superadmin, Read)
    assert check_user_permission(superadmin, List)
    assert check_user_permission(superadmin, Create)
    assert check_user_permission(superadmin, CheckAvailability)

    # 2. User with Manage permission has all name tracker actions
    tracker_admin = DummyUser(permissions=[Manage])
    assert check_user_permission(tracker_admin, Manage)
    assert check_user_permission(tracker_admin, Read)
    assert check_user_permission(tracker_admin, List)
    assert check_user_permission(tracker_admin, View)
    assert check_user_permission(tracker_admin, Create)
    assert check_user_permission(tracker_admin, Update)
    assert check_user_permission(tracker_admin, Delete)
    assert check_user_permission(tracker_admin, CheckAvailability)

    # 3. User with NameTrackerRead has List, View, and CheckAvailability, but not mutating actions
    tracker_reader = DummyUser(permissions=[Read])
    assert check_user_permission(tracker_reader, Read)
    assert check_user_permission(tracker_reader, List)
    assert check_user_permission(tracker_reader, View)
    assert check_user_permission(tracker_reader, CheckAvailability)
    assert not check_user_permission(tracker_reader, Manage)
    assert not check_user_permission(tracker_reader, Write)
    assert not check_user_permission(tracker_reader, Create)
    assert not check_user_permission(tracker_reader, Update)
    assert not check_user_permission(tracker_reader, Delete)
    assert not check_user_permission(tracker_reader, Execute)

    # 4. User with CheckAvailability can check availability but cannot do other actions
    checker = DummyUser(permissions=[CheckAvailability])
    assert check_user_permission(checker, CheckAvailability)
    assert not check_user_permission(checker, List)
    assert not check_user_permission(checker, Create)
    assert not check_user_permission(checker, Delete)

    # 5. Default authenticated user (with FwRead) can list, view, and check availability
    default_user = DummyUser()
    assert check_user_permission(default_user, List)
    assert check_user_permission(default_user, View)
    assert check_user_permission(default_user, CheckAvailability)
    assert not check_user_permission(default_user, Create)
    assert not check_user_permission(default_user, Delete)


def test_name_tracker_endpoints_enforce_permissions(client: TestClient):
    """Verify name tracker endpoints enforce permissions via HTTP API."""
    settings.enable_auth = True
    with client as c:
        admin_headers = _get_superadmin_headers(c)
        reg_headers = _create_and_login_user(c, admin_headers, "regular_bob")

        # 1. Regular user cannot create name tracker entry
        resp = c.post(
            "/api/v1/name-tracker",
            json={
                "name": "test-perm-name",
                "module": "test_mod",
            },
            headers=reg_headers,
        )
        assert resp.status_code == 403
        assert "Permission denied" in resp.text

        # 2. Superadmin can create name tracker entry
        resp = c.post(
            "/api/v1/name-tracker",
            json={
                "name": "test-perm-name",
                "module": "test_mod",
            },
            headers=admin_headers,
        )
        assert resp.status_code == 200, resp.text
        entry_id = resp.json()["data"]["id"]

        # 3. Regular user can view name tracker entry
        resp = c.get(
            f"/api/v1/name-tracker/{entry_id}",
            headers=reg_headers,
        )
        assert resp.status_code == 200

        # 4. Regular user can list name tracker entries
        resp = c.get(
            "/api/v1/name-tracker",
            headers=reg_headers,
        )
        assert resp.status_code == 200

        # 5. Regular user can check name availability
        resp = c.get(
            "/api/v1/name-tracker/_check-availability?name=another-avail-name",
            headers=reg_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["available"] is True

        # 6. Regular user cannot update name tracker entry
        resp = c.put(
            f"/api/v1/name-tracker/{entry_id}",
            json={"module": "updated_mod"},
            headers=reg_headers,
        )
        assert resp.status_code == 403

        # 7. Regular user cannot delete name tracker entry
        resp = c.delete(
            f"/api/v1/name-tracker/{entry_id}",
            headers={
                "X-RESOURCE-NAME": "test-perm-name",
                **reg_headers,
            },
        )
        assert resp.status_code == 403


def test_name_tracker_endpoints_with_granted_permissions(client: TestClient):
    """Verify users with granted service permissions can access allowed endpoints."""
    settings.enable_auth = True
    with client as c:
        admin_headers = _get_superadmin_headers(c)
        manager_headers = _create_and_login_user(c, admin_headers, "tracker_manager")
        reader_headers = _create_and_login_user(c, admin_headers, "tracker_reader")
        checker_headers = _create_and_login_user(c, admin_headers, "avail_checker")

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
                "/api/v1/name-tracker",
                json={
                    "name": "mgr-tracker-item",
                    "module": "mgr_mod",
                },
                headers=manager_headers,
            )
            assert resp.status_code == 200, resp.text
            created_id = resp.json()["data"]["id"]

            # Can update
            resp = c.put(
                f"/api/v1/name-tracker/{created_id}",
                json={"module": "updated_mgr_mod"},
                headers=manager_headers,
            )
            assert resp.status_code == 200

            # Can check availability
            resp = c.get(
                "/api/v1/name-tracker/_check-availability?name=mgr-tracker-item",
                headers=manager_headers,
            )
            assert resp.status_code == 200
            assert resp.json()["available"] is False

            # Can delete
            resp = c.delete(
                f"/api/v1/name-tracker/{created_id}",
                headers={
                    "X-RESOURCE-NAME": "mgr-tracker-item",
                    **manager_headers,
                },
            )
            assert resp.status_code == 200

        # 2. User with Read permission (read-only control)
        # Create an entry as admin
        r_resp = c.post(
            "/api/v1/name-tracker",
            json={
                "name": "view-target-item",
                "module": "target_mod",
            },
            headers=admin_headers,
        )
        assert r_resp.status_code == 200
        target_id = r_resp.json()["data"]["id"]

        with patch("mindweaver.fw.permission.get_user_permissions", side_effect=_mock_perms([Read])):
            # Can list
            resp = c.get(
                "/api/v1/name-tracker",
                headers=reader_headers,
            )
            assert resp.status_code == 200

            # Can view
            resp = c.get(
                f"/api/v1/name-tracker/{target_id}",
                headers=reader_headers,
            )
            assert resp.status_code == 200

            # Can check availability
            resp = c.get(
                "/api/v1/name-tracker/_check-availability?name=view-target-item",
                headers=reader_headers,
            )
            assert resp.status_code == 200
            assert resp.json()["available"] is False

            # CANNOT create
            resp = c.post(
                "/api/v1/name-tracker",
                json={
                    "name": "illegal-tracker-item",
                    "module": "illegal_mod",
                },
                headers=reader_headers,
            )
            assert resp.status_code == 403

            # CANNOT update
            resp = c.put(
                f"/api/v1/name-tracker/{target_id}",
                json={"module": "updated_by_viewer"},
                headers=reader_headers,
            )
            assert resp.status_code == 403

            # CANNOT delete
            resp = c.delete(
                f"/api/v1/name-tracker/{target_id}",
                headers={
                    "X-RESOURCE-NAME": "view-target-item",
                    **reader_headers,
                },
            )
            assert resp.status_code == 403

        # 3. User with only CheckAvailability permission
        with patch("mindweaver.fw.permission.get_user_permissions", side_effect=_mock_perms([CheckAvailability])):
            # Checker cannot create
            resp = c.post(
                "/api/v1/name-tracker",
                json={
                    "name": "checker-create-attempt",
                    "module": "checker_mod",
                },
                headers=checker_headers,
            )
            assert resp.status_code == 403

            # Checker CAN check availability
            resp = c.get(
                "/api/v1/name-tracker/_check-availability?name=view-target-item",
                headers=checker_headers,
            )
            assert resp.status_code == 200
            assert resp.json()["available"] is False
