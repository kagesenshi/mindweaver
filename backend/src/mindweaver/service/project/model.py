# SPDX-FileCopyrightText: Copyright © 2025 Mohd Izhar Firdaus Bin Ismail
# SPDX-License-Identifier: AGPLv3+

from typing import Optional
from sqlmodel import Field
from sqlalchemy import String
from mindweaver.service import NamedBase


class Project(NamedBase, table=True):
    __tablename__ = "mw_project"
    description: str = Field(default="", nullable=True)
    k8s_namespace: Optional[str] = Field(
        default=None, sa_type=String(length=32), nullable=True
    )
    k8s_cluster_id: int = Field(foreign_key="mw_k8s_cluster.id")
