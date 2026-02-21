import pytest
from datetime import datetime
from pydantic import ValidationError
from sqlmodel import Field, SQLModel, create_engine
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy.ext.asyncio import create_async_engine
from mindweaver.platform_service.base import (
    PlatformStateBase,
    PlatformBase,
    PlatformService,
)
from mindweaver.service.project import Project, K8sClusterType
from mindweaver.config import settings
from pytest_postgresql.executor import PostgreSQLExecutor
from psycopg.connection import Connection


# Define a concrete model for testing
class MockPlatformState(PlatformStateBase, table=True):
    __tablename__ = "mw_test_platform_state"
    platform_id: int = Field(index=True)


class MockPlatform(PlatformBase, table=True):
    __tablename__ = "mw_test_platform"


class MockPlatformService(PlatformService[MockPlatform]):
    state_model = MockPlatformState

    @classmethod
    def model_class(cls):
        return MockPlatform


import pytest_asyncio


@pytest_asyncio.fixture(scope="function")
async def db_session(postgresql_proc: PostgreSQLExecutor, postgresql: Connection):
    """Create a test session for use in tests."""
    settings.db_host = postgresql_proc.host
    settings.db_port = postgresql_proc.port
    settings.db_name = postgresql_proc.dbname
    settings.db_user = postgresql_proc.user
    settings.db_pass = postgresql_proc.password
    # Set a test encryption key for password encryption
    settings.fernet_key = "EFw4cCjDgHhGuZAGlwXmQhXg134ZdHjb9SeqcszWeSU="

    engine = create_engine(settings.db_uri)
    SQLModel.metadata.create_all(engine)

    async_engine = create_async_engine(settings.db_async_uri)
    async with AsyncSession(async_engine) as session:
        yield session

    SQLModel.metadata.drop_all(engine)


def test_platform_state_instantiation():
    """Test that PlatformStateBase can be instantiated with all fields"""
    now = datetime.now()
    state = MockPlatformState(
        platform_id=1,
        status="online",
        active=True,
        message="Running smoothly",
        last_heartbeat=now,
        extra_data={"replica_count": 3},
    )
    assert state.platform_id == 1
    assert state.status == "online"
    assert state.active is True
    assert state.message == "Running smoothly"
    assert state.last_heartbeat == now
    assert state.extra_data == {"replica_count": 3}


def test_platform_state_defaults():
    """Test default values of PlatformStateBase"""
    state = MockPlatformState(platform_id=1)
    assert state.platform_id == 1
    assert state.status == "pending"
    assert state.active is True
    assert state.message is None
    assert state.last_heartbeat is None
    assert state.extra_data == {}


def test_platform_state_status_validation():
    """Test validation of status field using Literal values"""
    # Valid statuses
    for status in ["online", "offline", "pending", "error"]:
        state = MockPlatformState.model_validate({"platform_id": 1, "status": status})
        assert state.status == status

    # Invalid status
    with pytest.raises(ValidationError):
        MockPlatformState.model_validate({"status": "invalid"})


def test_platform_state_extra_data_json():
    """Test that extra_data accepts a dictionary (JSON)"""
    complex_data = {"nested": {"key": "value"}, "list": [1, 2, 3], "bool": True}
    state = MockPlatformState(platform_id=1, extra_data=complex_data)
    assert state.extra_data == complex_data


@pytest.mark.asyncio
async def test_platform_service_state(db_session):
    """Test platform_state() method in PlatformService"""
    # Create required dependencies
    project = Project(
        name="test-project",
        title="Test Project",
        k8s_cluster_type=K8sClusterType.REMOTE,
        k8s_cluster_kubeconfig="apiVersion: v1",
    )
    db_session.add(project)
    await db_session.flush()
    await db_session.refresh(project)

    # Create a mock platform
    platform = MockPlatform(
        project_id=project.id,
        name="test-platform",
        title="Test Platform",
    )
    db_session.add(platform)
    await db_session.flush()
    await db_session.refresh(platform)

    # Create a mock state
    state = MockPlatformState(
        platform_id=platform.id, status="online", message="Running"
    )
    db_session.add(state)
    await db_session.flush()

    # Initialize service
    from fastapi import Request
    from unittest.mock import MagicMock

    request = MagicMock(spec=Request)
    service = MockPlatformService(request, db_session)

    # Test retrieval
    retrieved_state = await service.platform_state(platform)
    assert retrieved_state is not None
    assert retrieved_state.platform_id == platform.id
    assert retrieved_state.status == "online"

    # Test retrieval for platform without state
    other_platform = MockPlatform(
        project_id=project.id,
        name="other-platform",
        title="Other Platform",
    )
    db_session.add(other_platform)
    await db_session.flush()
    await db_session.refresh(other_platform)

    no_state = await service.platform_state(other_platform)
    assert no_state is None


def test_enforce_state_model():
    """Verify that subclassing PlatformService without state_model raises TypeError"""

    class MockPlatformEnforce(PlatformBase, table=True):
        __tablename__ = "mw_test_enforce_platform"

    with pytest.raises(TypeError, match="must define state_model"):

        class InvalidPlatformService(PlatformService[MockPlatformEnforce]):
            pass


def test_allow_intermediate_abc():
    """Verify that intermediate abstract classes don't need to define state_model"""
    import abc

    class IntermediateBase(PlatformService, abc.ABC):
        pass

    # This should not raise TypeError
    assert True
