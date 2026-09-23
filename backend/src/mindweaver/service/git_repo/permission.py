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
    """Base permission for all operations on Git repository resources."""
    name: str = "git_repo:manage"


class Read(Manage, FwRead):
    """Permission to perform read-only operations on git repositories."""
    name: str = "git_repo:read"


class List(Read, FwList):
    """Permission to list git repositories."""
    name: str = "git_repo:list"


class View(Read, FwView):
    """Permission to view a specific git repository and its configuration."""
    name: str = "git_repo:view"


class Write(Manage, FwWrite):
    """Permission to perform mutating operations on git repositories."""
    name: str = "git_repo:write"


class Create(Write, FwCreate):
    """Permission to create a new git repository connection."""
    name: str = "git_repo:create"


class Update(Write, FwUpdate):
    """Permission to update an existing git repository connection."""
    name: str = "git_repo:update"


class Delete(Write, FwDelete):
    """Permission to delete an existing git repository connection."""
    name: str = "git_repo:delete"


class Execute(Manage, FwExecute):
    """Permission to execute actions and operational tasks on git repositories."""
    name: str = "git_repo:execute"


class TestConnection(Execute):
    """Permission to test connection to a git repository."""
    name: str = "git_repo:test_connection"


# Canonical Aliases
ManageGitRepo = Manage
ManageGitRepoPermission = Manage
GitRepo = Manage
GitRepoPermission = Manage
GitRepoRead = Read
GitRepoList = List
GitRepoView = View
GitRepoWrite = Write
GitRepoCreate = Create
GitRepoUpdate = Update
GitRepoDelete = Delete
GitRepoExecute = Execute
GitRepoTestConnection = TestConnection
