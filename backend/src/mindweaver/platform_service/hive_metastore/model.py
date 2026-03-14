# SPDX-FileCopyrightText: Copyright © 2026 Mohd Izhar Firdaus Bin Ismail
# SPDX-License-Identifier: AGPLv3+

from sqlmodel import Field
from mindweaver.platform_service.base import PlatformBase, PlatformStateBase
from pydantic import model_validator
from typing import Optional


class HiveMetastorePlatform(PlatformBase, table=True):
    __tablename__ = "mw_hive_metastore_platform"

    replica_count: int = Field(default=1)
    image: str = Field(default="ghcr.io/kagesenshi/mindweaver/hive-metastore:latest")

    # Resource configuration
    cpu_request: float = Field(default=0.5)
    cpu_limit: float = Field(default=1.0)
    mem_request: float = Field(default=1.0)
    mem_limit: float = Field(default=2.0)

    # Database configuration
    database_id: int = Field(foreign_key="mw_pgsql_platform.id")

    # Iceberg configuration
    iceberg_enabled: bool = Field(default=True)
    iceberg_port: int = Field(default=9001)

    @model_validator(mode="after")
    def validate_resource_limits(self) -> "HiveMetastorePlatform":
        if self.cpu_request > self.cpu_limit:
            raise ValueError("CPU request cannot be greater than CPU limit")
        if self.mem_request > self.mem_limit:
            raise ValueError("Memory request cannot be greater than Memory limit")
        return self


class HiveMetastorePlatformState(PlatformStateBase, table=True):
    __tablename__ = "mw_hive_metastore_platform_state"
    platform_id: int = Field(foreign_key="mw_hive_metastore_platform.id", index=True)

    hms_uri: Optional[str] = Field(default=None)
    iceberg_uri: Optional[str] = Field(default=None)
