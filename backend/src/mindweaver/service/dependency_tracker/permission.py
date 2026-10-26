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
    """Base permission for all operations on Dependency Tracker resources."""
    name: str = "dependency_tracker:manage"


class Read(Manage, FwRead):
    """Permission to perform read-only operations on dependency tracker."""
    name: str = "dependency_tracker:read"


class List(Read, FwList):
    """Permission to list dependency tracker entries."""
    name: str = "dependency_tracker:list"


class View(Read, FwView):
    """Permission to view a specific dependency tracker entry."""
    name: str = "dependency_tracker:view"


class Write(Manage, FwWrite):
    """Permission to perform mutating operations on dependency tracker."""
    name: str = "dependency_tracker:write"


class Create(Write, FwCreate):
    """Permission to create a new dependency tracker entry."""
    name: str = "dependency_tracker:create"


class Update(Write, FwUpdate):
    """Permission to update an existing dependency tracker entry."""
    name: str = "dependency_tracker:update"


class Delete(Write, FwDelete):
    """Permission to delete an existing dependency tracker entry."""
    name: str = "dependency_tracker:delete"


class Execute(Manage, FwExecute):
    """Permission to execute actions on dependency tracker."""
    name: str = "dependency_tracker:execute"


# Canonical Aliases
ManageDependencyTracker = Manage
ManageDependencyTrackerPermission = Manage
DependencyTracker = Manage
DependencyTrackerPermission = Manage
DependencyTrackerRead = Read
DependencyTrackerList = List
DependencyTrackerView = View
DependencyTrackerWrite = Write
DependencyTrackerCreate = Create
DependencyTrackerUpdate = Update
DependencyTrackerDelete = Delete
DependencyTrackerExecute = Execute
