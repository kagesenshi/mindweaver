# SPDX-FileCopyrightText: Copyright © 2026 Mohd Izhar Firdaus Bin Ismail
# SPDX-License-Identifier: AGPLv3+

from datetime import datetime
from typing import Optional
from sqlmodel import Field
from sqlalchemy import DateTime, String
from mindweaver.fw.model import Base, ts_now


class NameTracker(Base, table=True):
    __tablename__ = "mw_name_tracker"

    name: str = Field(
        sa_type=String(length=32),
        unique=True,
        index=True,
    )
    module: str = Field(
        sa_type=String(length=100),
    )
    last_seen: datetime = Field(
        default_factory=ts_now,
        sa_type=DateTime(timezone=True),
    )
