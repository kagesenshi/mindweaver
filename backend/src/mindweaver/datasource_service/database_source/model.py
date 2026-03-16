# SPDX-FileCopyrightText: Copyright © 2026 Mohd Izhar Firdaus Bin Ismail
# SPDX-License-Identifier: AGPLv3+

from typing import Optional
from sqlalchemy import String
from sqlmodel import Field
from ..base import DataSourceBase


class DatabaseSource(DataSourceBase, table=True):
    __tablename__ = "mw_database_source"

    engine: str = Field(
        sa_type=String(length=50),
        description="Database engine (e.g. postgresql, mysql, trino, mongodb)"
    )
    host: str = Field(sa_type=String(length=255))
    port: Optional[int] = Field(default=None)
    database: Optional[str] = Field(
        default=None,
        sa_type=String(length=255),
        description="Database name"
    )
    schema_name: Optional[str] = Field(
        default=None,
        sa_type=String(length=255),
        description="Default schema"
    )
