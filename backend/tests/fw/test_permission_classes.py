# SPDX-FileCopyrightText: Copyright © 2026 Mohd Izhar Firdaus Bin Ismail
# SPDX-License-Identifier: AGPLv3+

import pytest
from typing import Optional
from starlette.requests import Request
from mindweaver.config import settings
from mindweaver.fw.model import Base
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
    require,
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


class DummyModel(Base):
    """Mock model object for context tests."""
    project_id: int = 10
    owner_id: int = 100


class ProjectScopedWrite(Write):
    """Permission restricted to project_id == 10."""
    name: str = "project_scoped_write"

    @classmethod
    def check_context(cls, user=None, context: Optional[Base] = None, request=None) -> bool:
        if context is None:
            return True
        return getattr(context, "project_id", None) == 10


class ProjectScopedUpdate(ProjectScopedWrite, Update):
    """Update permission for project scoped resource."""
    name: str = "project_scoped_update"


def test_permission_class_check_context():
    """Verify permission classes with check_context evaluate model context."""
    superadmin = DummyUser(is_superadmin=True)
    scoped_user = DummyUser(is_superadmin=False, permissions=[ProjectScopedWrite])
    normal_user = DummyUser(is_superadmin=False)

    matching_model = DummyModel(id=1, project_id=10)
    other_model = DummyModel(id=2, project_id=99)

    # Scoped user has permission for matching project, but not other project
    assert check_user_permission(scoped_user, ProjectScopedUpdate, context=matching_model)
    assert not check_user_permission(scoped_user, ProjectScopedUpdate, context=other_model)
    assert check_user_permission(scoped_user, ProjectScopedUpdate, context=None)

    # Superadmin bypasses context restriction
    assert check_user_permission(superadmin, ProjectScopedUpdate, context=other_model)

    # Normal user does not have write regardless of context
    assert not check_user_permission(normal_user, ProjectScopedUpdate, context=matching_model)


def test_user_get_permissions_with_context():
    """Verify user with get_permissions(context) returns context-aware permissions."""
    class ContextAwareUser:
        def __init__(self, user_id: int):
            self.id = user_id
            self.is_superadmin = False

        def get_permissions(self, context: Optional[Base]):
            if context is not None and getattr(context, "owner_id", None) == self.id:
                return [Read, Write]
            return [Read]

    user = ContextAwareUser(user_id=100)
    owned_model = DummyModel(id=1, owner_id=100)
    other_model = DummyModel(id=2, owner_id=999)

    # Owned model gets Read + Write (View, Update, Delete)
    assert check_user_permission(user, Update, context=owned_model)
    assert check_user_permission(user, Delete, context=owned_model)
    assert check_user_permission(user, View, context=owned_model)

    # Other model only gets Read (View, List), not Write
    assert not check_user_permission(user, Update, context=other_model)
    assert not check_user_permission(user, Delete, context=other_model)
    assert check_user_permission(user, View, context=other_model)


def test_get_user_permissions_requires_context():
    """Verify get_user_permissions requires context argument."""
    class StrictContextUser:
        def __init__(self, perms):
            self.perms = perms
            self.is_superadmin = False

        def get_permissions(self, context: Optional[Base]):
            if context is not None and getattr(context, "id", None) == 1:
                return self.perms
            return [Read]

    user = StrictContextUser(perms=[Write])
    special_model = DummyModel(id=1)
    other_model = DummyModel(id=2)

    # Calling without context parameter must raise TypeError
    with pytest.raises(TypeError):
        get_user_permissions(user)  # type: ignore

    # Calling with context works
    assert get_user_permissions(user, special_model) == [Write]
    assert get_user_permissions(user, other_model) == [Read]
    assert get_user_permissions(user, None) == [Read]


@pytest.mark.asyncio
async def test_has_permission_with_context():
    """Verify has_permission handles context explicitly, positionally, and from request state."""
    old_auth = settings.enable_auth
    try:
        settings.enable_auth = True
        scoped_user = DummyUser(is_superadmin=False, permissions=[ProjectScopedWrite])

        scope = {"type": "http", "method": "POST", "path": "/test", "headers": []}
        req = Request(scope)
        req.state.user = scoped_user

        matching_model = DummyModel(id=1, project_id=10)
        other_model = DummyModel(id=2, project_id=99)

        # 1. Explicit keyword context
        assert await has_permission(req, ProjectScopedUpdate, context=matching_model)
        assert not await has_permission(req, ProjectScopedUpdate, context=other_model)

        # 2. Positional context argument: has_permission(request, perm, context)
        assert await has_permission(req, ProjectScopedUpdate, matching_model)
        assert not await has_permission(req, ProjectScopedUpdate, other_model)

        # 3. Context resolved from request.state.context
        req.state.context = matching_model
        assert await has_permission(req, ProjectScopedUpdate)
        req.state.context = other_model
        assert not await has_permission(req, ProjectScopedUpdate)
        delattr(req.state, "context")

        # 4. Context resolved from request.state.model
        req.state.model = matching_model
        assert await has_permission(req, ProjectScopedUpdate)
        req.state.model = other_model
        assert not await has_permission(req, ProjectScopedUpdate)
    finally:
        settings.enable_auth = old_auth


@pytest.mark.asyncio
async def test_require_dependency_with_context():
    """Verify require dependency enforces permissions with context and context_getter."""
    from fastapi import HTTPException

    old_auth = settings.enable_auth
    try:
        settings.enable_auth = True
        scoped_user = DummyUser(is_superadmin=False, permissions=[ProjectScopedWrite])

        scope = {"type": "http", "method": "POST", "path": "/test", "headers": []}
        req = Request(scope)
        req.state.user = scoped_user

        matching_model = DummyModel(id=1, project_id=10)
        other_model = DummyModel(id=2, project_id=99)

        # 1. require with static context
        checker_pass = require(ProjectScopedUpdate, context=matching_model).dependency
        await checker_pass(req, session=None)  # Should not raise

        checker_fail = require(ProjectScopedUpdate, context=other_model).dependency
        with pytest.raises(HTTPException) as exc_info:
            await checker_fail(req, session=None)
        assert exc_info.value.status_code == 403

        # 2. require with context_getter
        checker_getter = require(
            ProjectScopedUpdate,
            context_getter=lambda r, s: matching_model
        ).dependency
        await checker_getter(req, session=None)  # Should not raise

        checker_getter_fail = require(
            ProjectScopedUpdate,
            context_getter=lambda r, s: other_model
        ).dependency
        with pytest.raises(HTTPException) as exc_info:
            await checker_getter_fail(req, session=None)
        assert exc_info.value.status_code == 403

        # 3. require with context from req.state.context
        req.state.context = matching_model
        checker_state = require(ProjectScopedUpdate).dependency
        await checker_state(req, session=None)  # Should not raise

        req.state.context = other_model
        with pytest.raises(HTTPException) as exc_info:
            await checker_state(req, session=None)
        assert exc_info.value.status_code == 403
    finally:
        settings.enable_auth = old_auth


