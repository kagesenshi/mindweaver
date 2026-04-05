# SPDX-FileCopyrightText: Copyright © 2026 Mohd Izhar Firdaus Bin Ismail
# SPDX-License-Identifier: AGPLv3+

from mindweaver.service.base import NamedBase
from sqlmodel import Field
from typing import Optional
from pydantic import BaseModel, field_validator


# LDAP Configuration schema
class LdapConfigSchema(BaseModel):
    """Configuration schema for LDAP-based authentication."""

    server_url: str
    bind_dn: Optional[str] = None
    bind_password: Optional[str] = None
    user_search_base: str
    user_search_filter: str
    username_attr: str
    group_search_base: Optional[str] = None
    group_search_filter: Optional[str] = None
    group_member_attr: Optional[str] = None
    user_group_attr: Optional[str] = None
    verify_ssl: bool = True

    @field_validator("server_url")
    @classmethod
    def validate_server_url(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Server URL cannot be empty")
        v = v.strip()
        if not (v.startswith("ldap://") or v.startswith("ldaps://")):
            raise ValueError("Server URL must start with ldap:// or ldaps://")
        return v

    @field_validator("user_search_base")
    @classmethod
    def validate_user_search_base(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("User Search Base cannot be empty")
        return v.strip()


# Database model
class LdapConfig(NamedBase, table=True):
    __tablename__ = "mw_ldap_config"
    server_url: str
    bind_dn: Optional[str] = Field(default=None)
    bind_password: Optional[str] = Field(default=None)
    user_search_base: str
    user_search_filter: str
    username_attr: str
    group_search_base: Optional[str] = Field(default=None)
    group_search_filter: Optional[str] = Field(default=None)
    group_member_attr: Optional[str] = Field(default=None)
    user_group_attr: Optional[str] = Field(default=None)
    verify_ssl: bool = Field(default=True)
