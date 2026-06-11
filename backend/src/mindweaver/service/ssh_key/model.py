# SPDX-FileCopyrightText: Copyright © 2026 Mohd Izhar Firdaus Bin Ismail
# SPDX-License-Identifier: AGPLv3+

from mindweaver.service.base import ProjectScopedNamedBase
from sqlmodel import Field
from typing import Optional
from pydantic import BaseModel, field_validator


class SSHKeyConfig(BaseModel):
    """Configuration schema for validating SSH keys."""

    algorithm: str = "rsa"  # "rsa", "ed25519"
    key_size: Optional[int] = 4096  # 2048, 4096 (for RSA)

    @field_validator("algorithm")
    @classmethod
    def validate_algorithm(cls, v: str) -> str:
        v_lower = v.strip().lower()
        if v_lower not in ("rsa", "ed25519"):
            raise ValueError("Algorithm must be 'rsa' or 'ed25519'")
        return v_lower

    @field_validator("key_size")
    @classmethod
    def validate_key_size(cls, v: Optional[int]) -> Optional[int]:
        if v is not None and v not in (2048, 4096):
            raise ValueError("Key size must be 2048 or 4096")
        return v


class SSHKey(ProjectScopedNamedBase, table=True):
    __tablename__ = "mw_ssh_key"
    private_key: Optional[str] = Field(default=None)
    public_key: Optional[str] = Field(default=None)
    algorithm: str = Field(default="rsa")
    key_size: Optional[int] = Field(default=4096)
