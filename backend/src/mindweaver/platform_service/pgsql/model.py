# SPDX-FileCopyrightText: Copyright © 2026 Mohd Izhar Firdaus Bin Ismail
# SPDX-License-Identifier: AGPLv3+

from sqlmodel import Field
from mindweaver.platform_service.base import PlatformBase, PlatformStateBase
from pydantic import field_validator, model_validator
from typing import Optional


class PgSqlPlatform(PlatformBase, table=True):
    __tablename__ = "mw_pgsql_platform"

    instances: int = Field(default=3)
    storage_size: str = Field(default="1Gi")
    image: str = Field(default="ghcr.io/cloudnative-pg/postgresql:18")

    # Resource configuration
    cpu_request: float = Field(default=0.5)
    cpu_limit: float = Field(default=1.0)
    mem_request: float = Field(default=1.0)
    mem_limit: float = Field(default=2.0)

    # Backup configuration (using Barman Cloud Object Store)
    enable_backup: bool = Field(default=False)
    backup_destination: str | None = Field(default=None)
    backup_retention_policy: str = Field(default="30d")
    s3_storage_id: int | None = Field(default=None, foreign_key="mw_s3_storage.id")

    @field_validator("backup_destination")
    @classmethod
    def validate_backup_destination(cls, v: str | None) -> str | None:
        if v:
            if not v.startswith("s3://"):
                raise ValueError(
                    "Backup destination must be a valid S3 URI (starts with s3://)"
                )
            if v == "s3://":
                raise ValueError("Backup destination must include a bucket name")
        return v

    @field_validator("instances")
    @classmethod
    def validate_instances(cls, v: int) -> int:
        if v < 1 or v % 2 == 0:
            raise ValueError("Instances must be an odd number (1, 3, 5, ...)")
        return v

    @model_validator(mode="after")
    def validate_resource_limits(self) -> "PgSqlPlatform":
        if self.cpu_request > self.cpu_limit:
            raise ValueError("CPU request cannot be greater than CPU limit")
        if self.mem_request > self.mem_limit:
            raise ValueError("Memory request cannot be greater than Memory limit")
        return self


class PgSqlPlatformState(PlatformStateBase, table=True):
    __tablename__ = "mw_pgsql_platform_state"
    platform_id: int = Field(foreign_key="mw_pgsql_platform.id", index=True)

    db_user: Optional[str] = Field(default=None)
    db_pass: Optional[str] = Field(default=None)
    db_name: Optional[str] = Field(default=None)
    db_ca_crt: Optional[str] = Field(default=None)
