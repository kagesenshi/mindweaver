import pytest
from unittest.mock import AsyncMock, MagicMock
import sys
import os

# Add the frontend directory to the python path so we can import mindweaver_fe
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from mindweaver_fe.api_client import (
    APIClient,
    AIAgentClient,
    ChatClient,
    KnowledgeDBClient,
    DataSourceClient,
    LakehouseStorageClient,
    IngestionClient,
)


@pytest.fixture
def mock_api_client():
    client = MagicMock(spec=APIClient)
    client.list_all = AsyncMock(return_value=[])
    client.get = AsyncMock(return_value={})
    client.create = AsyncMock(return_value={})
    client.update = AsyncMock(return_value={})
    client.delete = AsyncMock(return_value=True)
    return client


@pytest.fixture
def mock_ai_agent_client(mock_api_client):
    client = MagicMock(spec=AIAgentClient)
    client.client = mock_api_client
    client.list_all = AsyncMock(return_value=[])
    client.get = AsyncMock(return_value={})
    client.create = AsyncMock(return_value={})
    client.update = AsyncMock(return_value={})
    client.delete = AsyncMock(return_value=True)
    return client


@pytest.fixture
def mock_chat_client(mock_api_client):
    client = MagicMock(spec=ChatClient)
    client.client = mock_api_client
    client.list_all = AsyncMock(return_value=[])
    client.get = AsyncMock(return_value={})
    client.create = AsyncMock(return_value={})
    client.update = AsyncMock(return_value={})
    client.delete = AsyncMock(return_value=True)
    return client


@pytest.fixture
def mock_knowledge_db_client(mock_api_client):
    client = MagicMock(spec=KnowledgeDBClient)
    client.client = mock_api_client
    client.list_all = AsyncMock(return_value=[])
    client.get = AsyncMock(return_value={})
    client.create = AsyncMock(return_value={})
    client.update = AsyncMock(return_value={})
    client.delete = AsyncMock(return_value=True)
    return client


@pytest.fixture
def mock_data_source_client(mock_api_client):
    client = MagicMock(spec=DataSourceClient)
    client.client = mock_api_client
    client.list_all = AsyncMock(return_value=[])
    client.get = AsyncMock(return_value={})
    client.create = AsyncMock(return_value={})
    client.update = AsyncMock(return_value={})
    client.delete = AsyncMock(return_value=True)
    client.test_connection = AsyncMock(return_value={"status": "success"})
    return client


@pytest.fixture
def mock_lakehouse_storage_client(mock_api_client):
    client = MagicMock(spec=LakehouseStorageClient)
    client.client = mock_api_client
    client.list_all = AsyncMock(return_value=[])
    client.get = AsyncMock(return_value={})
    client.create = AsyncMock(return_value={})
    client.update = AsyncMock(return_value={})
    client.delete = AsyncMock(return_value=True)
    client.test_connection = AsyncMock(return_value={"status": "success"})
    return client


@pytest.fixture
def mock_ingestion_client(mock_api_client):
    client = MagicMock(spec=IngestionClient)
    client.client = mock_api_client
    client.list_all = AsyncMock(return_value=[])
    client.get = AsyncMock(return_value={})
    client.create = AsyncMock(return_value={})
    client.update = AsyncMock(return_value={})
    client.delete = AsyncMock(return_value=True)
    client.execute_ingestion = AsyncMock(return_value={"status": "success"})
    client.list_runs = AsyncMock(return_value=[])
    return client


@pytest.fixture
def mock_project_state():
    """Mock ProjectState with a test project."""
    from mindweaver_fe.states.project_state import ProjectState

    mock_state = MagicMock(spec=ProjectState)
    mock_state.current_project = {
        "id": 1,
        "name": "Test Project",
        "title": "Test Project",
        "description": "Test project for unit tests",
    }
    return mock_state
