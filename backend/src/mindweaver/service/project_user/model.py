# SPDX-FileCopyrightText: Copyright © 2026 Mohd Izhar Firdaus Bin Ismail
# SPDX-License-Identifier: AGPLv3+

from typing import Optional
from sqlmodel import Field, SQLModel
from sqlalchemy import String
from pydantic import model_validator
from mindweaver.service.base import ProjectScopedBase


class ProjectLocalUserSchema(SQLModel):
    """
    Schema model for project local user fields validation.
    """
    project_id: int = Field(foreign_key="mw_project.id")
    username: str = Field(sa_type=String(255), unique=True, index=True)
    email: str = Field(sa_type=String(255), unique=True, index=True)
    password: Optional[str] = Field(default=None, exclude=True)
    password_confirm: Optional[str] = Field(default=None, exclude=True)

    @model_validator(mode="after")
    def validate_password_confirm(self) -> "ProjectLocalUserSchema":
        """
        Validate that password and password_confirm fields match.
        """
        if self.password is not None and self.password != "__REDACTED__":
            if self.password != self.password_confirm:
                raise ValueError("Passwords do not match")
        return self


class ProjectLocalUser(ProjectScopedBase, table=True):
    """
    Database model representing a project-scoped local user.
    """

    __tablename__ = "mw_project_local_user"

    username: str = Field(sa_type=String(255), unique=True, index=True)
    email: str = Field(sa_type=String(255), unique=True, index=True)

    password_hash_bcrypt: Optional[str] = Field(default=None, sa_type=String(255))
    password_hash_md5: Optional[str] = Field(default=None, sa_type=String(255))
    password_hash_sha256: Optional[str] = Field(default=None, sa_type=String(255))
    password_hash_sha512: Optional[str] = Field(default=None, sa_type=String(255))

    password: Optional[str] = Field(default=None, exclude=True, sa_column=None)

    @property
    def name(self) -> str:
        """
        Return the username as name to satisfy framework deletion check.
        """
        return self.username


