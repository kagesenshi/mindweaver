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
    """Base permission for all operations on SSH Key resources."""

    name: str = "ssh_key:manage"


class Read(Manage, FwRead):
    """Permission to perform read-only operations on ssh keys."""

    name: str = "ssh_key:read"


class List(Read, FwList):
    """Permission to list ssh keys."""

    name: str = "ssh_key:list"


class View(Read, FwView):
    """Permission to view a specific ssh key and its public key/configuration."""

    name: str = "ssh_key:view"


class Write(Manage, FwWrite):
    """Permission to perform mutating operations on ssh keys."""

    name: str = "ssh_key:write"


class Create(Write, FwCreate):
    """Permission to create a new ssh key."""

    name: str = "ssh_key:create"


class Update(Write, FwUpdate):
    """Permission to update an existing ssh key."""

    name: str = "ssh_key:update"


class Delete(Write, FwDelete):
    """Permission to delete an existing ssh key."""

    name: str = "ssh_key:delete"


class Execute(Manage, FwExecute):
    """Permission to execute actions on ssh keys."""

    name: str = "ssh_key:execute"


# Canonical Aliases (SSHKey*)
ManageSSHKey = Manage
ManageSSHKeyPermission = Manage
SSHKey = Manage
SSHKeyPermission = Manage
SSHKeyRead = Read
SSHKeyList = List
SSHKeyView = View
SSHKeyWrite = Write
SSHKeyCreate = Create
SSHKeyUpdate = Update
SSHKeyDelete = Delete
SSHKeyExecute = Execute

# Canonical Aliases (SshKey*)
ManageSshKey = Manage
ManageSshKeyPermission = Manage
SshKey = Manage
SshKeyPermission = Manage
SshKeyRead = Read
SshKeyList = List
SshKeyView = View
SshKeyWrite = Write
SshKeyCreate = Create
SshKeyUpdate = Update
SshKeyDelete = Delete
SshKeyExecute = Execute
