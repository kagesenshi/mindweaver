# SPDX-FileCopyrightText: Copyright © 2026 Mohd Izhar Firdaus Bin Ismail
# SPDX-License-Identifier: AGPLv3+

from sqlmodel import Field
from sqlalchemy_utils import JSONType
from pydantic import model_validator, BaseModel, field_validator, ConfigDict
from mindweaver.platform_service.base import PlatformBase, PlatformStateBase
import secrets
from typing import Optional, Any


class AirflowRoleMapping(BaseModel):
    """
    Mapping of external identity to Airflow role.
    """
    entity: str
    role: str

    @field_validator("role")
    @classmethod
    def validate_role(cls, v: str) -> str:
        valid_roles = ["Admin", "User", "Op", "Viewer", "Public"]
        if v not in valid_roles:
            raise ValueError(f"Invalid role: {v}. Must be one of {valid_roles}")
        return v


class AirflowPlatform(PlatformBase, table=True):
    """
    Apache Airflow platform configuration.
    """
    __tablename__ = "mw_airflow_platform"
    model_config = ConfigDict(validate_assignment=True)

    # Chart version selection (targetRevision in Application manifest)
    chart_version: str = Field(default="1.22.0")
    # Image override - when True, the image field overrides the default image
    override_image: bool = Field(default=False)
    image: str = Field(default="ghcr.io/kagesenshi/mindweaver/airflow:latest")

    # Deploy Redis/Valkey for Celery broker by default
    redis_enabled: bool = Field(default=True)

    # S3 Storage for remote logging (no PVC)
    s3_storage_id: Optional[int] = Field(default=None, foreign_key="mw_s3_storage.id")
    logs_s3_bucket: str = Field(default="")

    # Internal secrets
    # Initial password for the 'admin' user created by createUserJob
    admin_password: str = Field(default_factory=lambda: secrets.token_urlsafe(16))
    # Fernet key for encrypting connections/variables in the database
    fernet_key: str = Field(default_factory=lambda: secrets.token_urlsafe(32))
    # Webserver secret key for Airflow 3+ JWT signing
    webserver_secret_key: str = Field(default_factory=lambda: secrets.token_urlsafe(32))

    # OIDC Login Configuration
    oidc_enabled: bool = Field(default=False)
    oidc_client_secret: str = Field(default_factory=lambda: secrets.token_urlsafe(32))

    # PostgreSQL dependency (mandatory for Airflow metadata)
    platform_pgsql_id: int = Field(foreign_key="mw_pgsql_platform.id")

    # Auth Role Mapping (OIDC/LDAP to Airflow)
    auth_role_mapping: list[dict] = Field(default_factory=list, sa_type=JSONType())

    # DAGs git-sync configuration
    dags_git_sync_enabled: bool = Field(default=False)
    dags_git_repo: str = Field(default="")
    dags_git_branch: str = Field(default="main")
    dags_git_subpath: str = Field(default="dags")
    dags_git_secret: Optional[str] = Field(default=None)

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
                    res.append(AirflowRoleMapping(**item).model_dump())
                elif isinstance(item, AirflowRoleMapping):
                    res.append(item.model_dump())
                else:
                    res.append(item)
            return res
        return v

    @model_validator(mode="after")
    def validate_resource_limits(self) -> "AirflowPlatform":
        if self.cpu_request is not None and self.cpu_limit is not None:
            if self.cpu_request > self.cpu_limit:
                raise ValueError("CPU request cannot be greater than CPU limit")
        if self.mem_request is not None and self.mem_limit is not None:
            if self.mem_request > self.mem_limit:
                raise ValueError("Memory request cannot be greater than Memory limit")
        return self


class AirflowPlatformState(PlatformStateBase, table=True):
    """
    Apache Airflow platform state.
    """
    __tablename__ = "mw_airflow_platform_state"
    platform_id: int = Field(foreign_key="mw_airflow_platform.id", index=True)

    airflow_uri: Optional[str] = Field(default=None)
    airflow_uri_ipv6: Optional[str] = Field(default=None)

    admin_user: Optional[str] = Field(default=None)
    admin_password: Optional[str] = Field(default=None)
