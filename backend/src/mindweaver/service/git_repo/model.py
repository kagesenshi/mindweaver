# SPDX-FileCopyrightText: Copyright © 2026 Mohd Izhar Firdaus Bin Ismail
# SPDX-License-Identifier: AGPLv3+

from mindweaver.service.base import ProjectScopedNamedBase
from sqlmodel import Field
from typing import Optional
from pydantic import BaseModel, field_validator


class GitRepoConfig(BaseModel):
    """Configuration schema for validating external Git repositories."""

    url: str
    username: Optional[str] = None
    password: Optional[str] = None
    ssh_key_id: Optional[int] = None

    @field_validator("url")
    @classmethod
    def validate_url(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Git repository URL cannot be empty")
        # Accept HTTP, HTTPS, or SSH git URL patterns
        v_stripped = v.strip()
        if (
            not v_stripped.startswith("http://")
            and not v_stripped.startswith("https://")
            and not v_stripped.startswith("git@")
            and not v_stripped.startswith("ssh://")
        ):
            raise ValueError("Invalid Git repository URL format")
        return v_stripped


class GitRepo(ProjectScopedNamedBase, table=True):
    __tablename__ = "mw_git_repo"

    url: str
    username: Optional[str] = Field(default=None)
    password: Optional[str] = Field(default=None)
    ssh_key_id: Optional[int] = Field(default=None, foreign_key="mw_ssh_key.id", index=True)
