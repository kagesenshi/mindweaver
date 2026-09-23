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
    """Base permission for all operations on Project User resources."""
    name: str = "project_user:manage"


class Read(Manage, FwRead):
    """Permission to perform read-only operations on project users."""
    name: str = "project_user:read"


class List(Read, FwList):
    """Permission to list project users."""
    name: str = "project_user:list"


class View(Read, FwView):
    """Permission to view a specific project user."""
    name: str = "project_user:view"


class Write(Manage, FwWrite):
    """Permission to perform mutating operations on project users."""
    name: str = "project_user:write"


class Create(Write, FwCreate):
    """Permission to create a new project user."""
    name: str = "project_user:create"


class Update(Write, FwUpdate):
    """Permission to update an existing project user."""
    name: str = "project_user:update"


class Delete(Write, FwDelete):
    """Permission to delete an existing project user."""
    name: str = "project_user:delete"


class Execute(Manage, FwExecute):
    """Permission to execute actions on project users."""
    name: str = "project_user:execute"


# Canonical Aliases (ProjectUser*)
ManageProjectUser = Manage
ManageProjectUserPermission = Manage
ProjectUser = Manage
ProjectUserPermission = Manage
ProjectUserRead = Read
ProjectUserList = List
ProjectUserView = View
ProjectUserWrite = Write
ProjectUserCreate = Create
ProjectUserUpdate = Update
ProjectUserDelete = Delete
ProjectUserExecute = Execute

# Canonical Aliases (ProjectLocalUser*)
ManageProjectLocalUser = Manage
ManageProjectLocalUserPermission = Manage
ProjectLocalUser = Manage
ProjectLocalUserPermission = Manage
ProjectLocalUserRead = Read
ProjectLocalUserList = List
ProjectLocalUserView = View
ProjectLocalUserWrite = Write
ProjectLocalUserCreate = Create
ProjectLocalUserUpdate = Update
ProjectLocalUserDelete = Delete
ProjectLocalUserExecute = Execute
