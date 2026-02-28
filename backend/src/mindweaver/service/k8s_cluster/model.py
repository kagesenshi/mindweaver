# SPDX-FileCopyrightText: Copyright © 2026 Mohd Izhar Firdaus Bin Ismail
# SPDX-License-Identifier: AGPLv3+

import enum
from datetime import datetime
from typing import Optional, Any

from sqlmodel import Field, Column
from sqlalchemy import String, Enum as SQLEnum, DateTime
from sqlalchemy_utils import JSONType

from mindweaver.service import NamedBase
from mindweaver.fw.model import Base, ts_now


class K8sClusterType(enum.StrEnum):
    IN_CLUSTER = "in-cluster"
    REMOTE = "remote"


class K8sCluster(NamedBase, table=True):
    __tablename__ = "mw_k8s_cluster"
    description: str = Field(default="", nullable=True)

    type: K8sClusterType = Field(
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
    kubeconfig: Optional[str] = Field(default=None, sa_type=String)


class K8sClusterStatus(Base, table=True):
    __tablename__ = "mw_k8s_cluster_status"

    k8s_cluster_id: int = Field(foreign_key="mw_k8s_cluster.id", unique=True)
    status: str = Field(default="unknown")  # online, offline, error
    message: Optional[str] = Field(default=None)

    k8s_version: Optional[str] = Field(default=None)
    node_count: int = Field(default=0)
    nodes_status: dict[str, Any] = Field(default_factory=dict, sa_type=JSONType())

    cpu_total: float = Field(default=0.0)
    cpu_allocated: float = Field(default=0.0)
    ram_total: float = Field(default=0.0)
    ram_allocated: float = Field(default=0.0)

    argocd_installed: bool = Field(default=False)
    argocd_version: Optional[str] = Field(default=None)

    last_update: datetime = Field(
        default_factory=ts_now, sa_type=DateTime(timezone=True)
    )
