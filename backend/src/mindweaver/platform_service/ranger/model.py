# SPDX-FileCopyrightText: Copyright © 2026 Mohd Izhar Firdaus Bin Ismail
# SPDX-License-Identifier: AGPLv3+

from sqlalchemy import Column
from sqlalchemy_utils import JSONType
from sqlmodel import Field
from mindweaver.platform_service.base import PlatformBase, PlatformStateBase
from pydantic import model_validator
from typing import Optional


class RangerPlatform(PlatformBase, table=True):
    __tablename__ = "mw_ranger_platform"

    replica_count: int = Field(default=1)

    # Chart version selection (targetRevision in Application manifest)
    chart_version: str = Field(default="main")
    
    # Image override
    override_image: bool = Field(default=False)
    image: str = Field(default="docker.io/apache/ranger:2.8.0")

    # Resource configuration
    cpu_request: float = Field(default=1.0)
    cpu_limit: float = Field(default=2.0)
    mem_request: float = Field(default=2.0)
    mem_limit: float = Field(default=4.0)

    # Database configuration (PostgreSQL)
    database_id: int = Field(foreign_key="mw_pgsql_platform.id")

    # S3 Configuration (Audit store)
    s3_storage_id: Optional[int] = Field(default=None, foreign_key="mw_s3_storage.id")
    audit_s3_uri: str = Field(default="s3://ranger/audit")

    # Credentials (Encrypted)
    admin_password: str = Field(default="rangerR0cks!")
    keyadmin_password: str = Field(default="rangerR0cks!")
    tagsync_password: str = Field(default="rangerR0cks!")
    usersync_password: str = Field(default="rangerR0cks!")

    additional_properties: dict[str, str] = Field(
        default_factory=dict,
        sa_type=JSONType(),
        description="Additional properties for Ranger Admin",
    )

    @model_validator(mode="after")
    def validate_resource_limits(self) -> "RangerPlatform":
        """Validates resource requests do not exceed limits."""
        if self.cpu_request > self.cpu_limit:
            raise ValueError("CPU request cannot be greater than CPU limit")
        if self.mem_request > self.mem_limit:
            raise ValueError("Memory request cannot be greater than Memory limit")
        return self


class RangerPlatformState(PlatformStateBase, table=True):
    __tablename__ = "mw_ranger_platform_state"
    platform_id: int = Field(foreign_key="mw_ranger_platform.id", index=True)

    ranger_url: Optional[str] = Field(default=None)
