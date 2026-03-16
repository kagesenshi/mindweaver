# SPDX-FileCopyrightText: Copyright © 2026 Mohd Izhar Firdaus Bin Ismail
# SPDX-License-Identifier: AGPLv3+

from typing import Optional
from sqlalchemy import String, Text
from sqlmodel import Field
from ..base import DataSourceBase


class WebSource(DataSourceBase, table=True):
    __tablename__ = "mw_web_source"

    url: str = Field(
        sa_type=String(length=500),
        description="Base URL or Start URL"
    )
    allowed_domains: Optional[str] = Field(
        default=None,
        sa_type=Text,
        description="Comma separated list of allowed domains"
    )
    user_agent: Optional[str] = Field(
        default=None,
        sa_type=String(length=255)
    )
