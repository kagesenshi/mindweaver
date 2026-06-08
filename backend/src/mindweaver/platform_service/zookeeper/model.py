# SPDX-FileCopyrightText: Copyright © 2026 Mohd Izhar Firdaus Bin Ismail
# SPDX-License-Identifier: AGPLv3+

from typing import Optional
from sqlmodel import Field
from sqlalchemy_utils import JSONType
from pydantic import model_validator
from mindweaver.platform_service.base import PlatformBase, PlatformStateBase


class ZookeeperPlatform(PlatformBase, table=True):
    __tablename__ = "mw_zookeeper_platform"

    replica_count: int = Field(default=3)

    # Chart version selection (targetRevision in Application manifest)
    chart_version: str = Field(default="0.2.15")

    # Image override
    override_image: bool = Field(default=False)
    image: str = Field(default="pravega/zookeeper")
    image_tag: str = Field(default="0.2.15")

    # Storage configuration
    storage_size: str = Field(default="20Gi")

    # Resource configuration
    cpu_request: float = Field(default=0.5)
    cpu_limit: float = Field(default=1.0)
    mem_request: float = Field(default=1.0)
    mem_limit: float = Field(default=2.0)

    additional_properties: dict[str, str] = Field(
        default_factory=dict,
        sa_type=JSONType(),
        description="Additional properties for Zookeeper",
    )

    @model_validator(mode="after")
    def validate_resource_limits(self) -> "ZookeeperPlatform":
        """Validates resource requests do not exceed limits and replica count is valid."""
        if self.cpu_request > self.cpu_limit:
            raise ValueError("CPU request cannot be greater than CPU limit")
        if self.mem_request > self.mem_limit:
            raise ValueError("Memory request cannot be greater than Memory limit")
        if self.replica_count < 1 or self.replica_count > 9:
            raise ValueError("Replica count must be between 1 and 9")
        return self


class ZookeeperPlatformState(PlatformStateBase, table=True):
    __tablename__ = "mw_zookeeper_platform_state"
    platform_id: int = Field(foreign_key="mw_zookeeper_platform.id", index=True)

    zookeeper_url: Optional[str] = Field(default=None)
    zookeeper_url_ipv6: Optional[str] = Field(default=None)
