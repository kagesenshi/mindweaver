# SPDX-FileCopyrightText: Copyright © 2026 Mohd Izhar Firdaus Bin Ismail
# SPDX-License-Identifier: AGPLv3+

from typing import Optional
from sqlmodel import Field
from sqlalchemy_utils import JSONType
from pydantic import model_validator
from mindweaver.platform_service.base import PlatformBase, PlatformStateBase


class OpenSearchPlatform(PlatformBase, table=True):
    __tablename__ = "mw_opensearch_platform"

    replica_count: int = Field(default=1)

    # Chart version selection (targetRevision in Application manifest)
    chart_version: str = Field(default="2.20.0")

    # Image override
    override_image: bool = Field(default=False)
    image: str = Field(default="opensearchproject/opensearch")
    image_tag: str = Field(default="2.12.0")

    # Storage configuration
    storage_size: str = Field(default="10Gi")

    # Resource configuration
    cpu_request: float = Field(default=1.0)
    cpu_limit: float = Field(default=2.0)
    mem_request: float = Field(default=2.0)
    mem_limit: float = Field(default=4.0)

    # Credentials (Encrypted)
    admin_password: str = Field(default=None)

    additional_properties: dict[str, str] = Field(
        default_factory=dict,
        sa_type=JSONType(),
        description="Additional properties for OpenSearch",
    )

    @model_validator(mode="after")
    def validate_resource_limits(self) -> "OpenSearchPlatform":
        """Validates resource requests do not exceed limits and replica count is valid."""
        if self.cpu_request > self.cpu_limit:
            raise ValueError("CPU request cannot be greater than CPU limit")
        if self.mem_request > self.mem_limit:
            raise ValueError("Memory request cannot be greater than Memory limit")
        if self.replica_count < 1 or self.replica_count > 9 or self.replica_count % 2 == 0:
            raise ValueError("Replica count must be an odd number between 1 and 9")
        return self


class OpenSearchPlatformState(PlatformStateBase, table=True):
    __tablename__ = "mw_opensearch_platform_state"
    platform_id: int = Field(foreign_key="mw_opensearch_platform.id", index=True)

    opensearch_url: Optional[str] = Field(default=None)
    opensearch_url_ipv6: Optional[str] = Field(default=None)

    # Credentials (Encrypted in database)
    admin_password: Optional[str] = Field(default=None)
