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
from mindweaver.service.dependency_tracker.permission import (
    Manage,
    DependencyTracker,
    Read,
    List,
    View,
    Write,
    Create,
    Update,
    Delete,
    Execute,
    ManageDependencyTrackerPermission,
    ManageDependencyTracker,
    DependencyTrackerPermission,
    DependencyTrackerRead,
    DependencyTrackerList,
    DependencyTrackerView,
    DependencyTrackerWrite,
    DependencyTrackerCreate,
    DependencyTrackerUpdate,
    DependencyTrackerDelete,
    DependencyTrackerExecute,
)


class DummyUser:
    """Mock user class for permission testing."""

    def __init__(self, is_superadmin: bool = False, permissions: list | None = None):
        """Initialize mock user with superadmin status and permissions list."""
        self.is_superadmin = is_superadmin
        self.permissions = permissions


def test_dependency_tracker_permission_hierarchy():
    """Verify DependencyTracker permission classes inherit correctly from All, Permission, and fw classes."""
    assert issubclass(Manage, Permission)
    assert issubclass(Manage, All)

    # Read hierarchy
    assert issubclass(Read, Manage)
    assert issubclass(Read, FwRead)
    assert issubclass(List, Read)
    assert issubclass(List, Manage)
    assert issubclass(List, FwList)
    assert issubclass(View, Read)
    assert issubclass(View, Manage)
    assert issubclass(View, FwView)

    # Write hierarchy
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

    # Execute
    assert issubclass(Execute, Manage)
    assert not issubclass(Execute, Read)
    assert not issubclass(Execute, Write)
    assert issubclass(Execute, FwExecute)


def test_dependency_tracker_aliases():
    """Verify all canonical aliases are identical to the target permission class."""
    assert ManageDependencyTracker is Manage
    assert ManageDependencyTrackerPermission is Manage
    assert DependencyTracker is Manage
    assert DependencyTrackerPermission is Manage

    assert DependencyTrackerRead is Read
    assert DependencyTrackerList is List
    assert DependencyTrackerView is View
    assert DependencyTrackerWrite is Write
    assert DependencyTrackerCreate is Create
    assert DependencyTrackerUpdate is Update
    assert DependencyTrackerDelete is Delete
    assert DependencyTrackerExecute is Execute


def test_dependency_tracker_permission_registration():
    """Verify all dependency_tracker permissions are auto-registered in the global _NAME_TO_PERMISSION registry."""
    expected_names = [
        "dependency_tracker:manage",
        "dependency_tracker:read",
        "dependency_tracker:list",
        "dependency_tracker:view",
        "dependency_tracker:write",
        "dependency_tracker:create",
        "dependency_tracker:update",
        "dependency_tracker:delete",
        "dependency_tracker:execute",
    ]
    for name in expected_names:
        assert name in _NAME_TO_PERMISSION
        assert issubclass(_NAME_TO_PERMISSION[name], Permission)


def test_dependency_tracker_check_user_permission():
    """Test check_user_permission logic with dependency_tracker permissions."""
    user_manage = DummyUser(permissions=["dependency_tracker:manage"])
    assert check_user_permission(user_manage, Manage) is True
    assert check_user_permission(user_manage, Read) is True
    assert check_user_permission(user_manage, List) is True
    assert check_user_permission(user_manage, View) is True
    assert check_user_permission(user_manage, Write) is True
    assert check_user_permission(user_manage, Create) is True
    assert check_user_permission(user_manage, Update) is True
    assert check_user_permission(user_manage, Delete) is True
    assert check_user_permission(user_manage, Execute) is True

    user_read = DummyUser(permissions=["dependency_tracker:read"])
    assert check_user_permission(user_read, Read) is True
    assert check_user_permission(user_read, List) is True
    assert check_user_permission(user_read, View) is True
    assert check_user_permission(user_read, Manage) is False
    assert check_user_permission(user_read, Write) is False
    assert check_user_permission(user_read, Create) is False
    assert check_user_permission(user_read, Delete) is False

    user_write = DummyUser(permissions=["dependency_tracker:write"])
    assert check_user_permission(user_write, Write) is True
    assert check_user_permission(user_write, Create) is True
    assert check_user_permission(user_write, Update) is True
    assert check_user_permission(user_write, Delete) is True
    assert check_user_permission(user_write, Read) is False
    assert check_user_permission(user_write, List) is False
    assert check_user_permission(user_write, Manage) is False
