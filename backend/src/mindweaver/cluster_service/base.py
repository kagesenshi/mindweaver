from mindweaver.service.base import ProjectScopedNamedBase, ProjectScopedService
from mindweaver.service.k8s_cluster import K8sCluster
from sqlmodel import Field, select
from typing import TypeVar
from sqlmodel.ext.asyncio.session import AsyncSession


class ClusterBase(ProjectScopedNamedBase):
    k8s_cluster_id: int = Field(foreign_key="mw_k8s_cluster.id", index=True)


T = TypeVar("T", bound=ClusterBase)


class ClusterService(ProjectScopedService[T]):
    """Base service for cluster services"""

    async def apply(self, model: T):
        """used to deploy/upgrade the service"""
        raise NotImplementedError("apply() must be implemented")

    async def k8s_cluster(self, model: T) -> K8sCluster:
        """returns the associated K8sCluster model"""
        result = await self.session.execute(
            select(K8sCluster).where(K8sCluster.id == model.k8s_cluster_id)
        )
        cluster = result.scalar_one_or_none()
        if not cluster:
            raise ValueError(f"K8sCluster with id {model.k8s_cluster_id} not found")
        return cluster

    async def kubeconfig(self, model: T) -> str:
        """returns the kubeconfig string from the associated cluster"""
        cluster = await self.k8s_cluster(model)
        if not cluster.kubeconfig:
            raise ValueError(f"K8sCluster {cluster.name} has no kubeconfig")
        return cluster.kubeconfig
