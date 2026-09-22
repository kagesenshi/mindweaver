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
    _NAME_TO_PERMISSION,
)


class ManageProject(Permission):
    """Base permission for all operations on Project resources."""
    name: str = "project:manage"


class ViewProject(ManageProject):
    """Permission to perform view-only operations on projects."""
    name: str = "project:view_project"


class Read(ViewProject, FwRead):
    """Permission to perform read-only operations on projects."""
    name: str = "project:read"


class List(Read, FwList):
    """Permission to list projects."""
    name: str = "project:list"


class View(Read, FwView):
    """Permission to view a specific project and its properties."""
    name: str = "project:view"


class Write(ManageProject, FwWrite):
    """Permission to perform mutating operations on projects."""
    name: str = "project:write"


class Create(Write, FwCreate):
    """Permission to create a new project."""
    name: str = "project:create"


class Update(Write, FwUpdate):
    """Permission to update an existing project."""
    name: str = "project:update"


class Delete(Write, FwDelete):
    """Permission to delete an existing project."""
    name: str = "project:delete"


class Execute(ManageProject, FwExecute):
    """Permission to execute project-level actions and tasks."""
    name: str = "project:execute"


class Refresh(View):
    """Permission to refresh project status and poll clusters."""
    name: str = "project:refresh"


class DownloadCert(View):
    """Permission to download HAProxy certificates."""
    name: str = "project:download_cert"


class CertManager(View):
    """Permission to inspect project Cert Manager status."""
    name: str = "project:cert_manager"


class IssuerCert(View):
    """Permission to inspect and download project Issuer CA certificate."""
    name: str = "project:issuer_cert"


class CertificateDetails(View):
    """Permission to inspect project certificate details."""
    name: str = "project:certificate_details"


class RenewCertificate(Execute):
    """Permission to renew project certificates."""
    name: str = "project:renew_certificate"


# Canonical Aliases
ManageProjectPermission = ManageProject
ViewProjectPermission = ViewProject
Project = ManageProject
ProjectPermission = ManageProject
ProjectRead = Read
ProjectList = List
ProjectView = View
ProjectWrite = Write
ProjectCreate = Create
ProjectUpdate = Update
ProjectDelete = Delete
ProjectExecute = Execute
ProjectRefresh = Refresh
ProjectDownloadCert = DownloadCert
ProjectCertManager = CertManager
ProjectIssuerCert = IssuerCert
ProjectCertificateDetails = CertificateDetails
ProjectRenewCertificate = RenewCertificate

# String lookup aliases
_NAME_TO_PERMISSION["project"] = ManageProject
_NAME_TO_PERMISSION["manage_project"] = ManageProject
_NAME_TO_PERMISSION["view_project"] = ViewProject

