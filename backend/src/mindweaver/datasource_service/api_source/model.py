# SPDX-FileCopyrightText: Copyright © 2026 Mohd Izhar Firdaus Bin Ismail
# SPDX-License-Identifier: AGPLv3+

from typing import Any
from sqlalchemy import String
from sqlalchemy_utils import JSONType
from sqlmodel import Field
from ..base import DataSourceBase


class APISource(DataSourceBase, table=True):
    __tablename__ = "mw_api_source"

    base_url: str = Field(
        sa_type=String(length=500),
        description="Base URL"
    )
    api_type: str = Field(
        default="rest",
        sa_type=String(length=50),
        description="API Type (REST, GraphQL, SOAP)",
    )
    auth_type: str = Field(
        default="none",
        sa_type=String(length=50),
        description="Authentication Type",
    )
    headers: dict[str, Any] = Field(
        default={},
        sa_type=JSONType(),
        description="HTTP Headers",
    )
