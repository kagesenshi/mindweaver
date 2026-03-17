# SPDX-FileCopyrightText: Copyright © 2026 Mohd Izhar Firdaus Bin Ismail
# SPDX-License-Identifier: AGPLv3+

from sqlmodel import Field
from sqlalchemy_utils import JSONType
from pydantic import model_validator, BaseModel, field_validator, ConfigDict
from mindweaver.platform_service.base import PlatformBase, PlatformStateBase
import secrets
from typing import Optional, Any


class SupersetRoleMapping(BaseModel):
    """
    Mapping of external identity to Superset role.
    """
    entity: str
    role: str

    @field_validator("role")
    @classmethod
    def validate_role(cls, v: str) -> str:
        valid_roles = ["Admin", "Alpha", "Gamma", "sql_lab", "Public"]
        if v not in valid_roles:
            raise ValueError(f"Invalid role: {v}. Must be one of {valid_roles}")
        return v


class SupersetPlatform(PlatformBase, table=True):
    """
    Apache Superset platform configuration.
    """
    __tablename__ = "mw_superset_platform"
    model_config = ConfigDict(validate_assignment=True)

    # Chart version selection (targetRevision in Application manifest)
    chart_version: str = Field(default="0.15.0")
    # Image override - when True, the image field overrides the default image
    override_image: bool = Field(default=False)
    image: str = Field(default="ghcr.io/kagesenshi/mindweaver/superset:latest")

    # Internal secrets
    # Initial password for the 'admin' user created by init job
    admin_password: str = Field(default_factory=lambda: secrets.token_urlsafe(16))
    # SUPERSET_SECRET_KEY for flask-session and encryption
    superset_secret_key: str = Field(default_factory=lambda: secrets.token_urlsafe(32))

    # PostgreSQL dependency (mandatory for Superset metadata)
    platform_pgsql_id: int = Field(foreign_key="mw_pgsql_platform.id")
    
    # LDAP configuration (optional)
    ldap_config_id: Optional[int] = Field(default=None, foreign_key="mw_ldap_config.id")

    # Data Source selection (to be automatically created in Superset)
    database_source_ids: list[int] = Field(default_factory=list, sa_type=JSONType())
    trino_ids: list[int] = Field(default_factory=list, sa_type=JSONType())

    # Auth Role Mapping (OIDC/LDAP to Superset)
    auth_role_mapping: list[dict] = Field(default_factory=list, sa_type=JSONType())

    # Resource configuration
    cpu_request: float = Field(default=0.5)
    cpu_limit: float = Field(default=2.0)
    mem_request: float = Field(default=2.0)
    mem_limit: float = Field(default=4.0)

    @field_validator("auth_role_mapping", mode="before")
    @classmethod
    def validate_auth_role_mapping(cls, v: Any) -> list[dict]:
        if isinstance(v, list):
            res = []
            for item in v:
                if isinstance(item, dict):
                    # Validate against model
                    res.append(SupersetRoleMapping(**item).model_dump())
                elif isinstance(item, SupersetRoleMapping):
                    res.append(item.model_dump())
                else:
                    res.append(item)
            return res
        return v

    @model_validator(mode="after")
    def validate_resource_limits(self) -> "SupersetPlatform":
        if self.cpu_request is not None and self.cpu_limit is not None:
            if self.cpu_request > self.cpu_limit:
                raise ValueError("CPU request cannot be greater than CPU limit")
        if self.mem_request is not None and self.mem_limit is not None:
            if self.mem_request > self.mem_limit:
                raise ValueError("Memory request cannot be greater than Memory limit")
        return self


class SupersetPlatformState(PlatformStateBase, table=True):
    """
    Apache Superset platform state.
    """
    __tablename__ = "mw_superset_platform_state"
    platform_id: int = Field(foreign_key="mw_superset_platform.id", index=True)

    superset_uri: Optional[str] = Field(default=None)
    superset_uri_ipv6: Optional[str] = Field(default=None)

    admin_user: Optional[str] = Field(default=None)
    admin_password: Optional[str] = Field(default=None)
