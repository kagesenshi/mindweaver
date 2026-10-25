# SPDX-FileCopyrightText: Copyright © 2026 Mohd Izhar Firdaus Bin Ismail
# SPDX-License-Identifier: AGPLv3+

from mindweaver.fw.permission import (
    Permission,
    Read as FwRead,
    Write as FwWrite,
    List as FwList,
    View as FwView,
    Create as FwCreate,
    Update as FwUpdate,
    Delete as FwDelete,
    Execute as FwExecute,
)


class Manage(Permission):
    """Base permission for all operations on Auth resources."""

    name: str = "auth:manage"


class Read(Manage, FwRead):
    """Permission to perform read-only operations on auth."""

    name: str = "auth:read"


class List(Read, FwList):
    """Permission to list auth resources."""

    name: str = "auth:list"


class View(Read, FwView):
    """Permission to view a specific auth resource."""

    name: str = "auth:view"


class Write(Manage, FwWrite):
    """Permission to perform mutating operations on auth."""

    name: str = "auth:write"


class Create(Write, FwCreate):
    """Permission to create a new auth resource."""

    name: str = "auth:create"


class Update(Write, FwUpdate):
    """Permission to update an existing auth resource."""

    name: str = "auth:update"


class Delete(Write, FwDelete):
    """Permission to delete an existing auth resource."""

    name: str = "auth:delete"


class Execute(Manage, FwExecute):
    """Permission to execute auth actions and tasks."""

    name: str = "auth:execute"


class Me(View):
    """Permission to view current user's profile information."""

    name: str = "auth:me"


class UpdateMe(Update, Read):
    """Permission for current user to update their own profile."""

    name: str = "auth:updateme"


# Canonical Aliases (Auth*)
ManageAuth = Manage
ManageAuthPermission = Manage
Auth = Manage
AuthPermission = Manage
AuthRead = Read
AuthList = List
AuthView = View
AuthWrite = Write
AuthCreate = Create
AuthUpdate = Update
AuthDelete = Delete
AuthExecute = Execute
AuthMe = Me
AuthUpdateMe = UpdateMe
