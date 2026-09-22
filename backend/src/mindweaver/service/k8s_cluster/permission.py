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


class ManageK8sCluster(Permission):
    """Base permission for all operations on Kubernetes Cluster resources."""
    name: str = "k8s_cluster:manage"


class ViewK8sCluster(ManageK8sCluster):
    """Permission to perform view-only operations on k8s clusters."""
    name: str = "k8s_cluster:view_k8s_cluster"


class Read(ViewK8sCluster, FwRead):
    """Permission to perform read-only operations on k8s clusters."""
    name: str = "k8s_cluster:read"


class List(Read, FwList):
    """Permission to list k8s clusters."""
    name: str = "k8s_cluster:list"


class View(Read, FwView):
    """Permission to view a specific k8s cluster and its status."""
    name: str = "k8s_cluster:view"


class Write(ManageK8sCluster, FwWrite):
    """Permission to perform mutating operations on k8s clusters."""
    name: str = "k8s_cluster:write"


class Create(Write, FwCreate):
    """Permission to create a new k8s cluster."""
    name: str = "k8s_cluster:create"


class Update(Write, FwUpdate):
    """Permission to update an existing k8s cluster."""
    name: str = "k8s_cluster:update"


class Delete(Write, FwDelete):
    """Permission to delete an existing k8s cluster."""
    name: str = "k8s_cluster:delete"


class Execute(ManageK8sCluster, FwExecute):
    """Permission to execute k8s cluster actions and tasks."""
    name: str = "k8s_cluster:execute"


class Refresh(View):
    """Permission to refresh k8s cluster status."""
    name: str = "k8s_cluster:refresh"


# Canonical Aliases
ManageK8sClusterPermission = ManageK8sCluster
ViewK8sClusterPermission = ViewK8sCluster
K8sCluster = ManageK8sCluster
K8sClusterPermission = ManageK8sCluster
K8sClusterRead = Read
K8sClusterList = List
K8sClusterView = View
K8sClusterWrite = Write
K8sClusterCreate = Create
K8sClusterUpdate = Update
K8sClusterDelete = Delete
K8sClusterExecute = Execute
K8sClusterRefresh = Refresh
