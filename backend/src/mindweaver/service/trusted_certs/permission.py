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
    """Base permission for all operations on Trusted Certificate resources."""

    name: str = "trusted_cert:manage"


class Read(Manage, FwRead):
    """Permission to perform read-only operations on trusted certificates."""

    name: str = "trusted_cert:read"


class List(Read, FwList):
    """Permission to list trusted certificates."""

    name: str = "trusted_cert:list"


class View(Read, FwView):
    """Permission to view a specific trusted certificate."""

    name: str = "trusted_cert:view"


class Write(Manage, FwWrite):
    """Permission to perform mutating operations on trusted certificates."""

    name: str = "trusted_cert:write"


class Create(Write, FwCreate):
    """Permission to create a new trusted certificate."""

    name: str = "trusted_cert:create"


class Update(Write, FwUpdate):
    """Permission to update an existing trusted certificate."""

    name: str = "trusted_cert:update"


class Delete(Write, FwDelete):
    """Permission to delete an existing trusted certificate."""

    name: str = "trusted_cert:delete"


class Execute(Manage, FwExecute):
    """Permission to execute actions on trusted certificates."""

    name: str = "trusted_cert:execute"


class Decode(View):
    """Permission to decode and view certificate details."""

    name: str = "trusted_cert:decode"


# Canonical Aliases (TrustedCert*)
ManageTrustedCert = Manage
ManageTrustedCertPermission = Manage
TrustedCert = Manage
TrustedCertPermission = Manage
TrustedCertRead = Read
TrustedCertList = List
TrustedCertView = View
TrustedCertWrite = Write
TrustedCertCreate = Create
TrustedCertUpdate = Update
TrustedCertDelete = Delete
TrustedCertExecute = Execute
TrustedCertDecode = Decode

# Canonical Aliases (TrustedCerts*)
ManageTrustedCerts = Manage
ManageTrustedCertsPermission = Manage
TrustedCerts = Manage
TrustedCertsPermission = Manage
TrustedCertsRead = Read
TrustedCertsList = List
TrustedCertsView = View
TrustedCertsWrite = Write
TrustedCertsCreate = Create
TrustedCertsUpdate = Update
TrustedCertsDelete = Delete
TrustedCertsExecute = Execute
TrustedCertsDecode = Decode
