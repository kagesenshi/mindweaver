from sqlmodel import SQLModel, Field, Column
from typing import Optional, Annotated, AsyncGenerator
from pydantic import AfterValidator
from uuid import UUID
from uuid_extensions import uuid7
from datetime import datetime, timezone
from sqlalchemy_utils import UUIDType
from sqlalchemy import DateTime, String
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.ext.asyncio import AsyncEngine as SAAsyncEngine
from sqlalchemy.ext.asyncio import AsyncConnection as SAAsyncConnection
from sqlalchemy.ext.asyncio import AsyncSession as SAAsyncSession
from fastapi import Depends
import pendulum
import re
from ..config import settings

def ts_now():
    tz = pendulum.timezone(settings.timezone)
    return datetime.now(tz=tz)

def is_valid_name(name: str) -> str:
    if not name:
        raise ValueError("Name cannot be empty")
    if not re.match(r"^[a-z0-9\-]+$", name):
        raise ValueError("Name can only contain lowercase letters, numbers, and dash")
    if len(name) > 128:
        raise ValueError("Name cannot be longer than 128 characters")
    return name

class Base(SQLModel):
    id: Optional[int] = Field(default=None, primary_key=True)
    uuid: UUID = Field(default_factory=uuid7, sa_type=UUIDType())
    created: datetime = Field(default_factory=ts_now, sa_type=DateTime(timezone=True))
    modified: datetime = Field(default_factory=ts_now, sa_type=DateTime(timezone=True))

class NamedBase(Base):
    name: Annotated[str, AfterValidator(is_valid_name)] = Field(sa_type=String(length=128))
    title: str = Field(sa_type=String(length=500))

def get_engine() -> SAAsyncEngine:
    return create_async_engine(settings.db_async_uri)

AsyncEngine = Annotated[SAAsyncEngine, Depends(get_engine)]

async def get_connection(engine: AsyncEngine) -> AsyncGenerator[SAAsyncConnection]:
    async with engine.connect() as conn:
        yield conn

AsyncConnection = Annotated[SAAsyncConnection, Depends(get_connection)]

async def get_session(engine: AsyncEngine) -> AsyncGenerator[SAAsyncSession]:
    sessionmaker = async_sessionmaker(engine)
    async with sessionmaker() as session:
        yield session
        await session.commit()

AsyncSession = Annotated[SAAsyncSession, Depends(get_session)]