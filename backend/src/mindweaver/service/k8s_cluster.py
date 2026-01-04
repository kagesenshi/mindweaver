import enum
from typing import Optional

from .base import ProjectScopedNamedBase, ProjectScopedService
from sqlmodel import Field, Column
from sqlalchemy import String, Enum as SQLEnum


class K8sClusterType(enum.StrEnum):
    IN_CLUSTER = "in-cluster"
    REMOTE = "remote"


class K8sCluster(ProjectScopedNamedBase, table=True):
    __tablename__ = "mw_k8s_cluster"
    type: K8sClusterType = Field(
        sa_column=Column(
            SQLEnum(
                K8sClusterType,
                native_enum=False,
                values_callable=lambda x: [i.value for i in x],
            ),
            nullable=False,
            server_default=K8sClusterType.REMOTE.value,
        )
    )
    kubeconfig: Optional[str] = Field(default=None, sa_type=String)


class K8sClusterService(ProjectScopedService[K8sCluster]):
    @classmethod
    def model_class(cls) -> type[K8sCluster]:
        return K8sCluster


router = K8sClusterService.router()
