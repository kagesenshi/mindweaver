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
    """Base permission for all operations on LDAP Config resources."""
    name: str = "ldap_config:manage"


class Read(Manage, FwRead):
    """Permission to perform read-only operations on ldap configs."""
    name: str = "ldap_config:read"


class List(Read, FwList):
    """Permission to list ldap configs."""
    name: str = "ldap_config:list"


class View(Read, FwView):
    """Permission to view a specific ldap config and its properties."""
    name: str = "ldap_config:view"


class Write(Manage, FwWrite):
    """Permission to perform mutating operations on ldap configs."""
    name: str = "ldap_config:write"


class Create(Write, FwCreate):
    """Permission to create a new ldap config."""
    name: str = "ldap_config:create"


class Update(Write, FwUpdate):
    """Permission to update an existing ldap config."""
    name: str = "ldap_config:update"


class Delete(Write, FwDelete):
    """Permission to delete an existing ldap config."""
    name: str = "ldap_config:delete"


class Execute(Manage, FwExecute):
    """Permission to execute ldap config actions and tasks."""
    name: str = "ldap_config:execute"


class TestConnection(Execute):
    """Permission to test connection to an LDAP server."""
    name: str = "ldap_config:test_connection"


# Canonical Aliases
ManageLdapConfig = Manage
ManageLdapConfigPermission = Manage
LdapConfig = Manage
LdapConfigPermission = Manage
LdapConfigRead = Read
LdapConfigList = List
LdapConfigView = View
LdapConfigWrite = Write
LdapConfigCreate = Create
LdapConfigUpdate = Update
LdapConfigDelete = Delete
LdapConfigExecute = Execute
LdapConfigTestConnection = TestConnection
