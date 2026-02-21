import enum
from typing import Any, Optional
from . import NamedBase
from . import Service
from sqlmodel import Field, Column
from sqlalchemy import String, Enum as SQLEnum


class K8sClusterType(enum.StrEnum):
    IN_CLUSTER = "in-cluster"
    REMOTE = "remote"


class Project(NamedBase, table=True):
    __tablename__ = "mw_project"
    description: str = Field(default="", nullable=True)

    k8s_cluster_type: K8sClusterType = Field(
        default=K8sClusterType.REMOTE,
        sa_column=Column(
            SQLEnum(
                K8sClusterType,
                native_enum=False,
                values_callable=lambda x: [i.value for i in x],
            ),
            nullable=False,
            server_default=K8sClusterType.REMOTE.value,
        ),
    )
    k8s_cluster_kubeconfig: Optional[str] = Field(default=None, sa_type=String)


class ProjectService(Service[Project]):
    @classmethod
    def model_class(cls) -> type[Project]:
        return Project

    @classmethod
    def widgets(cls) -> dict[str, Any]:
        return {
            "description": {"order": 5, "column_span": 2},
            "k8s_cluster_type": {
                "order": 10,
                "type": "select",
                "options": [
                    {"label": "In-Cluster", "value": "in-cluster"},
                    {"label": "Remote", "value": "remote"},
                ],
                "label": "K8s Cluster Type",
            },
            "k8s_cluster_kubeconfig": {
                "order": 11,
                "type": "textarea",
                "column_span": 2,
                "label": "Kubeconfig",
            },
        }


router = ProjectService.router()
