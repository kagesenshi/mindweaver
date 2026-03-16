# SPDX-FileCopyrightText: Copyright © 2026 Mohd Izhar Firdaus Bin Ismail
# SPDX-License-Identifier: AGPLv3+

from typing import Optional, Any
from sqlalchemy import String
from sqlalchemy_utils import JSONType
from sqlmodel import Field
from ..base import DataSourceBase


class StreamingSource(DataSourceBase, table=True):
    __tablename__ = "mw_streaming_source"

    broker_type: str = Field(
        sa_type=String(length=50),
        description="Broker Type (Kafka, Kinesis, RabbitMQ)",
    )
    bootstrap_servers: str = Field(
        sa_type=String(length=500),
        description="Comma separated list of bootstrap servers"
    )
    topic: Optional[str] = Field(
        default=None,
        sa_type=String(length=255)
    )
    group_id: Optional[str] = Field(
        default=None,
        sa_type=String(length=255)
    )
    extra_config: dict[str, Any] = Field(
        default={},
        sa_type=JSONType(),
        description="Extra broker configuration",
    )
