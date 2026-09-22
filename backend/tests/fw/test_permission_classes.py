# SPDX-FileCopyrightText: Copyright © 2026 Mohd Izhar Firdaus Bin Ismail
# SPDX-License-Identifier: AGPLv3+

import pytest
from starlette.requests import Request
from mindweaver.config import settings
from mindweaver.fw.permission import (
    Permission,
    Read,
    Write,
    List,
    View,
    Create,
    Update,
    Delete,
    Execute,
    All,
    Admin,
    check_user_permission,
    get_user_permissions,
    has_permission,
)


class DummyUser:
    """Mock user for permission checking tests."""
    def __init__(self, is_superadmin=False, permissions=None):
        self.is_superadmin = is_superadmin
        self.permissions = permissions


def test_permission_class_hierarchy():
    """Verify that permission classes properly inherit from All and category classes."""
    # All is the root permission class
    assert issubclass(Permission, All)
    assert issubclass(Read, Permission)
    assert issubclass(Write, Permission)
    assert issubclass(Execute, Permission)

    assert issubclass(Read, All)
    assert issubclass(Write, All)
    assert issubclass(Execute, All)

    assert issubclass(List, Read)
    assert issubclass(View, Read)
    assert issubclass(List, Permission)
    assert issubclass(View, Permission)
    assert issubclass(List, All)
    assert issubclass(View, All)

    assert issubclass(Create, Write)
    assert issubclass(Update, Write)
    assert issubclass(Delete, Write)
    assert issubclass(Create, Permission)
    assert issubclass(Update, Permission)
    assert issubclass(Delete, Permission)
    assert issubclass(Create, All)
    assert issubclass(Update, All)
    assert issubclass(Delete, All)

    assert Admin is All

    # Verify no class attribute mappings on Permission class
    assert not hasattr(Permission, "LIST")
    assert not hasattr(Permission, "VIEW")
    assert not hasattr(Permission, "CREATE")
    assert not hasattr(Permission, "UPDATE")
    assert not hasattr(Permission, "DELETE")
    assert not hasattr(Permission, "EXECUTE")
    assert not hasattr(Permission, "READ")
    assert not hasattr(Permission, "WRITE")
    assert not hasattr(Permission, "ALL")
    assert not hasattr(Permission, "ADMIN")


def test_permission_inheritance_checking():
    """Verify check_user_permission grants access based on class hierarchy."""
    # 1. Superadmin has all permissions
    superadmin = DummyUser(is_superadmin=True)
    assert check_user_permission(superadmin, List)
    assert check_user_permission(superadmin, View)
    assert check_user_permission(superadmin, Create)
    assert check_user_permission(superadmin, Update)
    assert check_user_permission(superadmin, Delete)
    assert check_user_permission(superadmin, Execute)
    assert check_user_permission(superadmin, Read)
    assert check_user_permission(superadmin, Write)
    assert check_user_permission(superadmin, Permission)
    assert check_user_permission(superadmin, All)

    # User granted All has all permissions
    all_user = DummyUser(is_superadmin=False, permissions=[All])
    assert check_user_permission(all_user, List)
    assert check_user_permission(all_user, Create)
    assert check_user_permission(all_user, Delete)
    assert check_user_permission(all_user, Execute)

    # 2. Regular user defaults to Read (List + View)
    normal_user = DummyUser(is_superadmin=False)
    assert check_user_permission(normal_user, List)
    assert check_user_permission(normal_user, View)
    assert check_user_permission(normal_user, Read)
    assert not check_user_permission(normal_user, Create)
    assert not check_user_permission(normal_user, Update)
    assert not check_user_permission(normal_user, Delete)
    assert not check_user_permission(normal_user, Execute)
    assert not check_user_permission(normal_user, Write)

    # 3. User with Write permission should get Create, Update, Delete
    writer_user = DummyUser(is_superadmin=False, permissions=[Write])
    assert check_user_permission(writer_user, Create)
    assert check_user_permission(writer_user, Update)
    assert check_user_permission(writer_user, Delete)
    assert check_user_permission(writer_user, Write)
    assert not check_user_permission(writer_user, List)
    assert not check_user_permission(writer_user, View)
    assert not check_user_permission(writer_user, Execute)

    # 4. User with granular permission (e.g., only Create)
    creator_user = DummyUser(is_superadmin=False, permissions=[Create])
    assert check_user_permission(creator_user, Create)
    assert not check_user_permission(creator_user, Update)
    assert not check_user_permission(creator_user, Delete)
    assert not check_user_permission(creator_user, Write)

    # 5. Composite group permission
    class EditorRole(Permission):
        group = [Read, Create, Update]

    editor_user = DummyUser(is_superadmin=False, permissions=[EditorRole])
    assert check_user_permission(editor_user, List)
    assert check_user_permission(editor_user, View)
    assert check_user_permission(editor_user, Create)
    assert check_user_permission(editor_user, Update)
    assert not check_user_permission(editor_user, Delete)
    assert not check_user_permission(editor_user, Execute)


def test_permission_string_lookup():
    """Verify check_user_permission supports string lookups matching permission names."""
    normal_user = DummyUser(is_superadmin=False)
    assert check_user_permission(normal_user, "list")
    assert check_user_permission(normal_user, "view")
    assert not check_user_permission(normal_user, "create")
    assert not check_user_permission(normal_user, "delete")


@pytest.mark.asyncio
async def test_has_permission():
    """Verify has_permission checks user permission from request or explicit user."""
    old_auth = settings.enable_auth
    try:
        settings.enable_auth = True
        superadmin = DummyUser(is_superadmin=True)
        normal_user = DummyUser(is_superadmin=False)
        writer_user = DummyUser(is_superadmin=False, permissions=[Write])

        scope = {"type": "http", "method": "GET", "path": "/test", "headers": []}

        # 1. User object explicitly specified
        req = Request(scope)
        assert await has_permission(req, List, user=superadmin)
        assert await has_permission(req, Create, user=superadmin)
        assert await has_permission(req, List, user=normal_user)
        assert not await has_permission(req, Create, user=normal_user)
        assert await has_permission(req, Create, user=writer_user)
        assert not await has_permission(req, List, user=writer_user)

        # 2. User object not specified, retrieved from request.state.user
        req.state.user = writer_user
        assert await has_permission(req, Create)
        assert await has_permission(req, Update)
        assert not await has_permission(req, List)

        # 3. User object not specified, request has no user -> returns False
        empty_req = Request(scope)
        assert not await has_permission(empty_req, List)

        # 4. If auth is disabled, has_permission returns True
        settings.enable_auth = False
        assert await has_permission(empty_req, Create)
    finally:
        settings.enable_auth = old_auth
