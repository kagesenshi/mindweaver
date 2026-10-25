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
    """Base permission for all operations on Stack resources."""

    name: str = "stack:manage"


class Read(Manage, FwRead):
    """Permission to perform read-only operations on stacks."""

    name: str = "stack:read"


class List(Read, FwList):
    """Permission to list stacks."""

    name: str = "stack:list"


class View(Read, FwView):
    """Permission to view a specific stack."""

    name: str = "stack:view"


class Write(Manage, FwWrite):
    """Permission to perform mutating operations on stacks."""

    name: str = "stack:write"


class Create(Write, FwCreate):
    """Permission to create a new stack."""

    name: str = "stack:create"


class Update(Write, FwUpdate):
    """Permission to update an existing stack."""

    name: str = "stack:update"


class Delete(Write, FwDelete):
    """Permission to delete an existing stack."""

    name: str = "stack:delete"


class Execute(Manage, FwExecute):
    """Permission to execute stack actions and tasks."""

    name: str = "stack:execute"


# Canonical Aliases (Stack*)
ManageStack = Manage
ManageStackPermission = Manage
Stack = Manage
StackPermission = Manage
StackRead = Read
StackList = List
StackView = View
StackWrite = Write
StackCreate = Create
StackUpdate = Update
StackDelete = Delete
StackExecute = Execute

# Canonical Aliases (Stacks*)
ManageStacks = Manage
ManageStacksPermission = Manage
Stacks = Manage
StacksPermission = Manage
StacksRead = Read
StacksList = List
StacksView = View
StacksWrite = Write
StacksCreate = Create
StacksUpdate = Update
StacksDelete = Delete
StacksExecute = Execute
