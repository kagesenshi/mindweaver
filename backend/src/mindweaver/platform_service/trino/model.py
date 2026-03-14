# SPDX-FileCopyrightText: Copyright © 2026 Mohd Izhar Firdaus Bin Ismail
# SPDX-License-Identifier: AGPLv3+

from sqlmodel import Field
from sqlalchemy_utils import JSONType
from mindweaver.platform_service.base import PlatformBase, PlatformStateBase
from pydantic import model_validator
from typing import Optional, Any


class TrinoPlatform(PlatformBase, table=True):
    __tablename__ = "mw_trino_platform"

    replica_count: int = Field(default=1)
    image: str = Field(default="trinodb/trino:latest")

    # Resource configuration
    cpu_request: float = Field(default=0.5)
    cpu_limit: float = Field(default=2.0)
    mem_request: float = Field(default=2.0)
    mem_limit: float = Field(default=4.0)

    # HMS configuration
    hms_id: Optional[int] = Field(default=None, foreign_key="mw_hive_metastore_platform.id")

    # Data sources for Trino catalog
    data_source_ids: list[int] = Field(default_factory=list, sa_type=JSONType())

    # Auto-scaling (KEDA)
    keda_enabled: bool = Field(default=True)
    keda_min_replicas: int = Field(default=1)
    keda_max_replicas: int = Field(default=10)

    @model_validator(mode="after")
    def validate_resource_limits(self) -> "TrinoPlatform":
        if self.cpu_request > self.cpu_limit:
            raise ValueError("CPU request cannot be greater than CPU limit")
        if self.mem_request > self.mem_limit:
            raise ValueError("Memory request cannot be greater than Memory limit")
        if self.keda_min_replicas > self.keda_max_replicas:
            raise ValueError("KEDA minimum replicas cannot be greater than maximum replicas")
        return self


class TrinoPlatformState(PlatformStateBase, table=True):
    __tablename__ = "mw_trino_platform_state"
    platform_id: int = Field(foreign_key="mw_trino_platform.id", index=True)

    trino_uri: Optional[str] = Field(default=None)
