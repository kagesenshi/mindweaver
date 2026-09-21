# SPDX-FileCopyrightText: Copyright © 2026 Mohd Izhar Firdaus Bin Ismail
# SPDX-License-Identifier: AGPLv3+

import secrets
from typing import Optional
from pydantic import field_validator, model_validator
from sqlmodel import Field
from mindweaver.platform_service.base import PlatformBase, PlatformStateBase


class DorisPlatform(PlatformBase, table=True):
    """Configuration model for Apache Doris platform service."""
    __tablename__ = "mw_doris_platform"

    fe_replicas: int = Field(default=3)
    be_replicas: int = Field(default=3)
    fe_storage_size: str = Field(default="10Gi")
    be_storage_size: str = Field(default="50Gi")

    # Frontend (FE) resource configuration
    fe_cpu_request: float = Field(default=0.5)
    fe_cpu_limit: float = Field(default=2.0)
    fe_mem_request: float = Field(default=2.0)
    fe_mem_limit: float = Field(default=4.0)

    # Backend (BE) resource configuration
    be_cpu_request: float = Field(default=0.5)
    be_cpu_limit: float = Field(default=2.0)
    be_mem_request: float = Field(default=2.0)
    be_mem_limit: float = Field(default=4.0)

    # Authentication credentials
    admin_password: str = Field(default_factory=lambda: secrets.token_urlsafe(16))

    @field_validator("fe_replicas")
    @classmethod
    def validate_fe_replicas(cls, v: int) -> int:
        """Validates that FE replicas is an odd positive number for quorum."""
        if v < 1 or v % 2 == 0:
            raise ValueError("FE replicas must be an odd positive number (1, 3, 5, ...)")
        return v

    @field_validator("be_replicas")
    @classmethod
    def validate_be_replicas(cls, v: int) -> int:
        """Validates that BE replicas is at least 1."""
        if v < 1:
            raise ValueError("BE replicas must be at least 1")
        return v

    @model_validator(mode="after")
    def validate_resource_limits(self) -> "DorisPlatform":
        """Validates that resource requests do not exceed resource limits for FE and BE."""
        if self.fe_cpu_request > self.fe_cpu_limit:
            raise ValueError("FE CPU request cannot be greater than FE CPU limit")
        if self.fe_mem_request > self.fe_mem_limit:
            raise ValueError("FE Memory request cannot be greater than FE Memory limit")
        if self.be_cpu_request > self.be_cpu_limit:
            raise ValueError("BE CPU request cannot be greater than BE CPU limit")
        if self.be_mem_request > self.be_mem_limit:
            raise ValueError("BE Memory request cannot be greater than BE Memory limit")
        return self


class DorisPlatformState(PlatformStateBase, table=True):
    """Runtime state tracking model for Apache Doris platform service."""
    __tablename__ = "mw_doris_platform_state"
    platform_id: int = Field(foreign_key="mw_doris_platform.id", index=True)

    query_uri: Optional[str] = Field(default=None)
    fe_http_uri: Optional[str] = Field(default=None)
    admin_user: Optional[str] = Field(default="root")
    admin_password: Optional[str] = Field(default=None)
