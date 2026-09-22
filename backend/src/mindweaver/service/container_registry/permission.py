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


class ManageContainerRegistry(Permission):
    """Base permission for all operations on Container Registry resources."""
    name: str = "container_registry:manage"


class ViewContainerRegistry(ManageContainerRegistry):
    """Permission to perform view-only operations on container registries."""
    name: str = "container_registry:view_container_registry"


class Read(ViewContainerRegistry, FwRead):
    """Permission to perform read-only operations on container registries."""
    name: str = "container_registry:read"


class List(Read, FwList):
    """Permission to list container registries."""
    name: str = "container_registry:list"


class View(Read, FwView):
    """Permission to view a specific container registry and its configuration."""
    name: str = "container_registry:view"


class Write(ManageContainerRegistry, FwWrite):
    """Permission to perform mutating operations on container registries."""
    name: str = "container_registry:write"


class Create(Write, FwCreate):
    """Permission to create a new container registry connection."""
    name: str = "container_registry:create"


class Update(Write, FwUpdate):
    """Permission to update an existing container registry connection."""
    name: str = "container_registry:update"


class Delete(Write, FwDelete):
    """Permission to delete an existing container registry connection."""
    name: str = "container_registry:delete"


class Execute(ManageContainerRegistry, FwExecute):
    """Permission to execute actions and operational tasks on container registries."""
    name: str = "container_registry:execute"


class TestConnection(Execute):
    """Permission to test connection to a container registry."""
    name: str = "container_registry:test_connection"


# Canonical Aliases
ManageContainerRegistryPermission = ManageContainerRegistry
ViewContainerRegistryPermission = ViewContainerRegistry
ContainerRegistry = ManageContainerRegistry
ContainerRegistryPermission = ManageContainerRegistry
ContainerRegistryRead = Read
ContainerRegistryList = List
ContainerRegistryView = View
ContainerRegistryWrite = Write
ContainerRegistryCreate = Create
ContainerRegistryUpdate = Update
ContainerRegistryDelete = Delete
ContainerRegistryExecute = Execute
ContainerRegistryTestConnection = TestConnection
