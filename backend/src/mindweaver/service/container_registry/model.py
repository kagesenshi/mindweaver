# SPDX-FileCopyrightText: Copyright © 2026 Mohd Izhar Firdaus Bin Ismail
# SPDX-License-Identifier: AGPLv3+

from mindweaver.service.base import ProjectScopedNamedBase
from sqlmodel import Field
from typing import Optional
from pydantic import BaseModel, field_validator


class ContainerRegistryConfig(BaseModel):
    """Configuration schema for validating Container Registry connections."""

    url: str
    username: str
    password: Optional[str] = None

    @field_validator("url")
    @classmethod
    def validate_url(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Registry URL cannot be empty")
        return v.strip()

    @field_validator("username")
    @classmethod
    def validate_username(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Username cannot be empty")
        return v.strip()


class ContainerRegistry(ProjectScopedNamedBase, table=True):
    __tablename__ = "mw_container_registry"

    url: str
    username: str
    password: Optional[str] = Field(default=None)
