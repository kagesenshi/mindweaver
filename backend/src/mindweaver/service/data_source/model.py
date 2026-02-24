# SPDX-FileCopyrightText: Copyright © 2026 Mohd Izhar Firdaus Bin Ismail
# SPDX-License-Identifier: AGPLv3+

from mindweaver.service.base import ProjectScopedNamedBase
from sqlalchemy import String, Text, Boolean
from sqlalchemy_utils import JSONType
from sqlmodel import Field
from typing import Any, Optional


class DataSource(ProjectScopedNamedBase, table=True):
    __tablename__ = "mw_datasource"

    description: Optional[str] = Field(
        default=None, sa_type=Text, sa_column_kwargs={"info": {"column_span": 2}}
    )
    driver: str = Field(
        sa_type=String(length=50),
        description="Source type / driver (e.g. web, postgresql, trino)",
        sa_column_kwargs={
            "info": {
                "widget": "select",
                "label": "Driver",
            }
        },
    )
    host: Optional[str] = Field(default=None, sa_type=String(length=255))
    port: Optional[int] = Field(default=None)
    resource: Optional[str] = Field(
        default=None,
        sa_type=String(length=500),
        description="Path, database name, schema, etc.",
    )
    login: Optional[str] = Field(default=None, sa_type=String(length=255))
    password: Optional[str] = Field(
        default=None,
        sa_type=String(length=500),
        sa_column_kwargs={"info": {"widget": "password"}},
    )
    enable_ssl: bool = Field(default=False, sa_type=Boolean)
    verify_ssl: bool = Field(default=False, sa_type=Boolean)
    parameters: dict[str, Any] = Field(
        default={},
        sa_type=JSONType(),
        description="Extra driver parameters (querystring format)",
    )
