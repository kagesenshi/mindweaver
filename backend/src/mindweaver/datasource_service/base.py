# SPDX-FileCopyrightText: Copyright © 2026 Mohd Izhar Firdaus Bin Ismail
# SPDX-License-Identifier: AGPLv3+

from typing import Any, Optional, Annotated, Union
from pydantic import BaseModel
from sqlalchemy import String, Text, Boolean
from sqlalchemy_utils import JSONType
from sqlmodel import Field
from fastapi import Depends
from mindweaver.service.base import ProjectScopedNamedBase, ProjectScopedService
from mindweaver.crypto import decrypt_password, EncryptionError


class DataSourceBase(ProjectScopedNamedBase):
    """Base class for all data sources."""
    description: Optional[str] = Field(default=None, sa_type=Text)
    login: Optional[str] = Field(
        default=None, 
        sa_type=String(length=255)
    )
    password: Optional[str] = Field(
        default=None,
        sa_type=String(length=500),
    )
    enable_ssl: bool = Field(default=False, sa_type=Boolean)
    verify_ssl: bool = Field(default=False, sa_type=Boolean)
    parameters: dict[str, Any] = Field(
        default={},
        sa_type=JSONType(),
        description="Extra parameters (querystring format)",
    )


class DataSourceServiceBase:
    """Base mixin for data source services."""

    @classmethod
    def redacted_fields(cls) -> list[str]:
        return ["password"]

    @classmethod
    def widgets(cls) -> dict[str, Any]:
        return {
            "description": {"order": 5, "column_span": 2},
            "login": {"order": 50},
            "password": {"order": 51, "type": "password"},
            "enable_ssl": {"order": 60},
            "verify_ssl": {"order": 61},
            "parameters": {"order": 100, "type": "key-value"},
        }


class TestConnectionRequest(BaseModel):
    """Generic request for connection testing with optional overrides."""
    # Common fields
    host: Optional[str] = None
    port: Optional[int] = None
    login: Optional[str] = None
    password: Optional[str] = None
    enable_ssl: Optional[bool] = None
    verify_ssl: Optional[bool] = None
    parameters: Optional[dict[str, Any]] = None
    
    # Specific fields
    engine: Optional[str] = None
    database: Optional[str] = None
    url: Optional[str] = None
    base_url: Optional[str] = None
    api_type: Optional[str] = None
    auth_type: Optional[str] = None
    broker_type: Optional[str] = None
    bootstrap_servers: Optional[str] = None


async def handle_test_connection(svc, model, data: Optional[TestConnectionRequest]):
    """Helper to merge model with overrides and test connection."""
    config = model.model_dump(exclude={"id", "uuid", "created", "modified", "project_id"})
    
    if data:
        overrides = data.model_dump(exclude_unset=True)
        for k, v in overrides.items():
            if v is not None:
                config[k] = v

    # Decrypt password if it's from DB and hasn't been overridden
    is_using_stored_password = not data or data.password is None
    if is_using_stored_password and model.password:
        try:
            config["password"] = decrypt_password(model.password)
        except EncryptionError:
            pass

    return await svc.perform_test_connection(config)


async def handle_test_connection_no_id(svc, data: TestConnectionRequest):
    """Helper for connection test without a saved record."""
    return await svc.perform_test_connection(data.model_dump(exclude_unset=True))
