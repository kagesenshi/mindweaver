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


class ManageNameTracker(Permission):
    """Base permission for all operations on Name Tracker resources."""
    name: str = "name_tracker:manage"


class ViewNameTracker(ManageNameTracker):
    """Permission to perform view-only operations on name tracker."""
    name: str = "name_tracker:view_name_tracker"


class Read(ViewNameTracker, FwRead):
    """Permission to perform read-only operations on name tracker."""
    name: str = "name_tracker:read"


class List(Read, FwList):
    """Permission to list name tracker entries."""
    name: str = "name_tracker:list"


class View(Read, FwView):
    """Permission to view a specific name tracker entry."""
    name: str = "name_tracker:view"


class Write(ManageNameTracker, FwWrite):
    """Permission to perform mutating operations on name tracker."""
    name: str = "name_tracker:write"


class Create(Write, FwCreate):
    """Permission to create a new name tracker entry."""
    name: str = "name_tracker:create"


class Update(Write, FwUpdate):
    """Permission to update an existing name tracker entry."""
    name: str = "name_tracker:update"


class Delete(Write, FwDelete):
    """Permission to delete an existing name tracker entry."""
    name: str = "name_tracker:delete"


class Execute(ManageNameTracker, FwExecute):
    """Permission to execute actions on name tracker."""
    name: str = "name_tracker:execute"


class CheckAvailability(View):
    """Permission to check name availability."""
    name: str = "name_tracker:check_availability"


# Canonical Aliases
ManageNameTrackerPermission = ManageNameTracker
ViewNameTrackerPermission = ViewNameTracker
NameTracker = ManageNameTracker
NameTrackerPermission = ManageNameTracker
NameTrackerRead = Read
NameTrackerList = List
NameTrackerView = View
NameTrackerWrite = Write
NameTrackerCreate = Create
NameTrackerUpdate = Update
NameTrackerDelete = Delete
NameTrackerExecute = Execute
NameTrackerCheckAvailability = CheckAvailability
