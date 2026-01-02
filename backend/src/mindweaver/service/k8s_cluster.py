import enum
from typing import Optional

from .base import ProjectScopedNamedBase, ProjectScopedService
from sqlmodel import Field
from sqlalchemy import String


class K8sClusterType(str, enum.Enum):
    IN_CLUSTER = "in-cluster"
    REMOTE = "remote"


class K8sCluster(ProjectScopedNamedBase, table=True):
    __tablename__ = "mw_k8s_cluster"
    type: str = Field(default=K8sClusterType.REMOTE.value, sa_type=String)
    kubeconfig: Optional[str] = Field(default=None, sa_type=String)


class K8sClusterService(ProjectScopedService[K8sCluster]):
    @classmethod
    def model_class(cls) -> type[K8sCluster]:
        return K8sCluster


router = K8sClusterService.router()
