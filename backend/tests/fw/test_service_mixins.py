# SPDX-FileCopyrightText: Copyright © 2026 Mohd Izhar Firdaus Bin Ismail
# SPDX-License-Identifier: AGPLv3+

import pytest
from sqlmodel import Field, SQLModel, create_engine
from sqlalchemy.ext.asyncio import create_async_engine
from sqlmodel.ext.asyncio.session import AsyncSession
from mindweaver.fw.service import Service
from mindweaver.fw.model import NamedBase
from mindweaver.crypto import decrypt_password
from mindweaver.fw.hash import verify_password
from mindweaver.config import settings
from unittest.mock import MagicMock
from fastapi import Request
from pytest_postgresql.executor import PostgreSQLExecutor


class MockModel(NamedBase, table=True):
    __tablename__ = "test_mock_model"
    password: str = Field(default="")
    secret_key: str = Field(default="")


class MockService(Service[MockModel]):
    @classmethod
    def model_class(cls):
        return MockModel

    @classmethod
    def hashed_fields(cls):
        return ["password"]

    @classmethod
    def redacted_fields(cls):
        return ["secret_key"]


@pytest.fixture
def mock_request():
    return MagicMock(spec=Request)


import pytest_asyncio


@pytest_asyncio.fixture
async def async_session(postgresql_proc: PostgreSQLExecutor, postgresql):
    settings.db_host = postgresql_proc.host
    settings.db_port = postgresql_proc.port
    settings.db_name = postgresql_proc.dbname
    settings.db_user = postgresql_proc.user
    settings.db_pass = postgresql_proc.password
    settings.fernet_key = "EFw4cCjDgHhGuZAGlwXmQhXg134ZdHjb9SeqcszWeSU="

    # Create tables synchronously
    sync_engine = create_engine(settings.db_uri)
    SQLModel.metadata.create_all(sync_engine)

    # Use async engine for tests
    async_engine = create_async_engine(settings.db_async_uri)
    async with AsyncSession(async_engine) as session:
        yield session
        await session.commit()

    SQLModel.metadata.drop_all(sync_engine)


@pytest.mark.asyncio
async def test_service_mixins_integration(mock_request, async_session):
    svc = MockService(mock_request, async_session)

    # Test Create
    data = MockModel(
        name="test", title="Test", password="password123", secret_key="secret123"
    )
    created = await svc.create(data)

    assert created.name == "test"
    # Verify password is hashed
    assert created.password != "password123"
    assert verify_password("password123", created.password)

    # Verify secret_key is encrypted
    assert created.secret_key != "secret123"
    assert decrypt_password(created.secret_key) == "secret123"

    # Test post_process_model (Redaction)
    processed = await svc.post_process_model(created)
    assert processed.password == "__REDACTED__"
    assert processed.secret_key == "__REDACTED__"

    # Test Update
    old_password = created.password
    old_secret = created.secret_key
    update_data = MockModel(
        name="test", title="Test", password="__REDACTED__", secret_key="new_secret"
    )
    updated = await svc.update(created.id, update_data)

    # Verify password kept old value (hashed)
    assert updated.password == old_password
    assert verify_password("password123", updated.password)

    # Verify secret_key updated to new encrypted value
    assert updated.secret_key != "new_secret"
    assert updated.secret_key != old_secret
    assert decrypt_password(updated.secret_key) == "new_secret"
