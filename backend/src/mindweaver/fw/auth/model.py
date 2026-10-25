# SPDX-FileCopyrightText: Copyright © 2026 Mohd Izhar Firdaus Bin Ismail
# SPDX-License-Identifier: AGPLv3+

from typing import Optional
from pydantic import BaseModel, Field as PydanticField
from sqlmodel import Field
from mindweaver.fw.model import NamedBase


class User(NamedBase, table=True):
    """User account entity stored in the database."""

    __tablename__ = "mw_user"
    name: Optional[str] = Field(index=True, unique=True, default=None, nullable=True)
    title: Optional[str] = Field(default=None, nullable=True)
    email: Optional[str] = Field(index=True, unique=True, default=None)
    password: Optional[str] = Field(default=None, nullable=True)
    display_name: Optional[str] = Field(default=None, nullable=True)
    is_active: bool = Field(default=True)
    is_superadmin: bool = Field(default=False)


class Token(BaseModel):
    """Access token response schema."""

    access_token: str
    token_type: str


class LoginRequest(BaseModel):
    """Payload schema for username and password authentication."""

    username: str
    password: str


class UserProfileUpdate(BaseModel):
    """Payload schema for updating user profile fields."""

    display_name: Optional[str] = None
    title: Optional[str] = None


class ChangePasswordRequest(BaseModel):
    """Payload schema for changing password."""

    password: str = PydanticField(min_length=8)
