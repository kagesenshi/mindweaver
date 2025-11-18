from sqlmodel import SQLModel, Field, Column
from typing import Optional
from uuid import UUID
from uuid_extensions import uuid7
from datetime import datetime, timezone
from sqlalchemy_utils import UUIDType
from sqlalchemy import DateTime, String

class Base(SQLModel):
    id: Optional[int] = Field(default=None, primary_key=True)
    uuid: UUID = Field(default_factory=uuid7, sa_type=UUIDType())
    created_date: datetime = Field(default_factory=lambda : datetime.now(tz=timezone.utc), sa_type=DateTime(timezone=True))
    modified_date: datetime = Field(default_factory=lambda : datetime.now(tz=timezone.utc), sa_type=DateTime(timezone=True))

class NamedBase(Base):
    name: str = Field(sa_type=String(length=128))
    title: str = Field(sa_type=String(length=500))