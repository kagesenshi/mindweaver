# SPDX-FileCopyrightText: Copyright © 2026 Mohd Izhar Firdaus Bin Ismail
# SPDX-License-Identifier: AGPLv3+

from sqlmodel import Field
from sqlalchemy_utils import JSONType
from mindweaver.platform_service.base import PlatformBase, PlatformStateBase
from pydantic import model_validator
import secrets
from typing import Optional, Any


class TrinoPlatform(PlatformBase, table=True):
    __tablename__ = "mw_trino_platform"

    replica_count: int = Field(default=1)
    
    # Chart version selection (targetRevision in Application manifest)
    chart_version: str = Field(default="1.41.0")

    # Image override - when True, the image field overrides the chart's default image
    override_image: bool = Field(default=False)
    image: str = Field(default="trinodb/trino:latest")

    # Resource configuration
    cpu_request: float = Field(default=0.5)
    cpu_limit: float = Field(default=2.0)
    mem_request: float = Field(default=2.0)
    mem_limit: float = Field(default=4.0)

    # HMS configuration
    hms_ids: list[int] = Field(default_factory=list, sa_type=JSONType())

    # Database sources for Trino catalog
    database_source_ids: list[int] = Field(default_factory=list, sa_type=JSONType())


    # Internal communication secret (required when auth is enabled)
    internal_shared_secret: str = Field(default_factory=lambda: secrets.token_hex(32))

    @model_validator(mode="after")
    def validate_resource_limits(self) -> "TrinoPlatform":
        if self.cpu_request > self.cpu_limit:
            raise ValueError("CPU request cannot be greater than CPU limit")
        if self.mem_request > self.mem_limit:
            raise ValueError("Memory request cannot be greater than Memory limit")
        return self

    @model_validator(mode="after")
    def validate_catalogs(self) -> "TrinoPlatform":
        """
        Ensure that at least one catalog is defined.
        """
        # At least one catalog check
        if not (self.hms_ids or self.database_source_ids):
            raise ValueError(
                "At least one catalog (Hive Metastore or Database Source) must be defined"
            )

        return self


class TrinoPlatformState(PlatformStateBase, table=True):
    __tablename__ = "mw_trino_platform_state"
    platform_id: int = Field(foreign_key="mw_trino_platform.id", index=True)

    trino_uri: Optional[str] = Field(default=None)
