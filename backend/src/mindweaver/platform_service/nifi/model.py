# SPDX-FileCopyrightText: Copyright © 2026 Mohd Izhar Firdaus Bin Ismail
# SPDX-License-Identifier: AGPLv3+

from sqlmodel import Field
from sqlalchemy_utils import JSONType
from mindweaver.platform_service.base import PlatformBase, PlatformStateBase
from pydantic import model_validator, BaseModel, field_validator, ConfigDict
from typing import Optional, Any


class NifiRoleMapping(BaseModel):
    """
    Mapping of external identity to NiFi role.
    """
    entity: str
    role: str

    @field_validator("role")
    @classmethod
    def validate_role(cls, v: str) -> str:
        valid_roles = ["Admin", "Reader"]
        if v not in valid_roles:
            raise ValueError(f"Invalid role: {v}. Must be one of {valid_roles}")
        return v


class NifiPlatform(PlatformBase, table=True):
    __tablename__ = "mw_nifi_platform"
    model_config = ConfigDict(validate_assignment=True)

    replica_count: int = Field(default=1)

    # Resource configuration
    cpu_request: float = Field(default=0.5)
    cpu_limit: float = Field(default=2.0)
    mem_request: float = Field(default=2.0)
    mem_limit: float = Field(default=4.0)

    storage_size: str = Field(default="10Gi")

    auth_role_mapping: list[dict] = Field(default_factory=list, sa_type=JSONType())

    additional_properties: dict[str, Any] = Field(default_factory=dict, sa_type=JSONType())

    @field_validator("auth_role_mapping", mode="before")
    @classmethod
    def validate_auth_role_mapping(cls, v: Any) -> list[dict]:
        if isinstance(v, list):
            res = []
            for item in v:
                if isinstance(item, dict):
                    res.append(NifiRoleMapping(**item).model_dump())
                elif isinstance(item, NifiRoleMapping):
                    res.append(item.model_dump())
                else:
                    res.append(item)
            return res
        return v

    @model_validator(mode="after")
    def validate_resource_limits(self) -> "NifiPlatform":
        """Validate that request limit is not greater than resource limit"""
        if self.cpu_request is not None and self.cpu_limit is not None:
            if self.cpu_request > self.cpu_limit:
                raise ValueError("CPU request cannot be greater than CPU limit")
        if self.mem_request is not None and self.mem_limit is not None:
            if self.mem_request > self.mem_limit:
                raise ValueError("Memory request cannot be greater than Memory limit")
        return self



class NifiPlatformState(PlatformStateBase, table=True):
    __tablename__ = "mw_nifi_platform_state"
    platform_id: int = Field(foreign_key="mw_nifi_platform.id", index=True)

    nifi_uri: Optional[str] = Field(default=None)
