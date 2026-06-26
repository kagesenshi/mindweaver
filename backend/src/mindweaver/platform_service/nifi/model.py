# SPDX-FileCopyrightText: Copyright © 2026 Mohd Izhar Firdaus Bin Ismail
# SPDX-License-Identifier: AGPLv3+

from sqlmodel import Field
from sqlalchemy_utils import JSONType
from mindweaver.platform_service.base import PlatformBase, PlatformStateBase
from pydantic import model_validator
from typing import Optional, Any


class NifiPlatform(PlatformBase, table=True):
    __tablename__ = "mw_nifi_platform"

    replica_count: int = Field(default=1)
    
    # Target revision (chart version, or we can use version tags of operator chart)
    chart_version: str = Field(default="1.17.0")

    override_image: bool = Field(default=False)
    image: str = Field(default="apache/nifi")
    image_tag: str = Field(default="2.9.0")

    # Resource configuration
    cpu_request: float = Field(default=0.5)
    cpu_limit: float = Field(default=2.0)
    mem_request: float = Field(default=2.0)
    mem_limit: float = Field(default=4.0)

    storage_size: str = Field(default="10Gi")

    additional_properties: dict[str, Any] = Field(default_factory=dict, sa_type=JSONType())

    @model_validator(mode="after")
    def validate_resource_limits(self) -> "NifiPlatform":
        """Validate that request limit is not greater than resource limit"""
        if self.cpu_request > self.cpu_limit:
            raise ValueError("CPU request cannot be greater than CPU limit")
        if self.mem_request > self.mem_limit:
            raise ValueError("Memory request cannot be greater than Memory limit")
        return self

    @model_validator(mode="after")
    def validate_nifi_version(self) -> "NifiPlatform":
        """Only allow NiFi 2.x versions to be validated"""
        version = self.image_tag
        if self.override_image and self.image and ":" in self.image:
            version = self.image.split(":")[-1]
        
        if not version.startswith("2."):
            raise ValueError("Only NiFi 2.x series is supported")
        return self


class NifiPlatformState(PlatformStateBase, table=True):
    __tablename__ = "mw_nifi_platform_state"
    platform_id: int = Field(foreign_key="mw_nifi_platform.id", index=True)

    nifi_uri: Optional[str] = Field(default=None)
