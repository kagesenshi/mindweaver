import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from mindweaver_fe.states.data_sources_state import DataSourcesState
from mindweaver_fe.states.knowledge_db_state import KnowledgeDBState
import reflex as rx


@pytest.mark.asyncio
async def test_load_initial_data(mock_data_source_client, mock_project_state):
    state = DataSourcesState()

    # Mock get_state for KnowledgeDBState and ProjectState
    mock_kdb_state = MagicMock(spec=KnowledgeDBState)
    mock_kdb_state.load_databases = AsyncMock()
    mock_kdb_state.all_databases = [{"id": 1, "name": "Test DB"}]

    async def mock_get_state(state_class):
        if state_class == KnowledgeDBState:
            return mock_kdb_state
        from mindweaver_fe.states.project_state import ProjectState

        if state_class == ProjectState:
            return mock_project_state
        return MagicMock()

    object.__setattr__(state, "get_state", mock_get_state)

    # Mock api client response
    mock_sources = [{"id": 1, "name": "Test Source", "type": "API"}]
    mock_data_source_client.list_all.return_value = mock_sources

    with patch(
        "mindweaver_fe.states.data_sources_state.data_source_client",
        mock_data_source_client,
    ):
        await state.load_initial_data()

    assert state.all_sources == mock_sources
    assert state.all_knowledge_dbs == [{"id": 1, "name": "Test DB"}]
    assert state.is_loading is False
    assert state.error_message == ""

    mock_kdb_state.load_databases.assert_called_once()
    mock_data_source_client.list_all.assert_called_once()


def test_open_create_modal():
    state = DataSourcesState()
    state.open_create_modal()

    assert state.show_source_modal is True
    assert state.is_editing is False
    assert state.form_data["name"] == ""
    assert state.form_data["source_type"] == "API"
    assert state.form_errors == {}


def test_open_edit_modal():
    state = DataSourcesState()
    source = {
        "id": 1,
        "uuid": "uuid-123",
        "name": "Test Source",
        "title": "Test Title",
        "type": "API",
        "parameters": {"base_url": "http://example.com", "api_key": "secret"},
        "created": "",
        "modified": "",
        "status": "Connected",
        "last_sync": "Yesterday",
    }

    state.open_edit_modal(source)

    assert state.show_source_modal is True
    assert state.is_editing is True
    assert state.source_to_edit["id"] == 1
    assert state.form_data["name"] == "Test Source"
    assert state.form_data["parameters"]["base_url"] == "http://example.com"
    # Password should not be cleared here as it's not a DB source, but let's check logic

    # Test DB source password clearing
    db_source = {
        "id": 2,
        "uuid": "uuid-456",
        "name": "DB Source",
        "title": "DB Title",
        "type": "Database",
        "parameters": {"host": "localhost", "password": "secret_pass"},
        "created": "",
        "modified": "",
        "status": "Connected",
        "last_sync": "Yesterday",
    }
    state.open_edit_modal(db_source)
    assert state.form_data["parameters"]["password"] == ""


@pytest.mark.asyncio
async def test_handle_submit_create(mock_data_source_client, mock_project_state):
    state = DataSourcesState()
    state.open_create_modal()

    # Mock get_state for ProjectState
    async def mock_get_state(state_class):
        from mindweaver_fe.states.project_state import ProjectState

        if state_class == ProjectState:
            return mock_project_state
        return MagicMock()

    object.__setattr__(state, "get_state", mock_get_state)

    form_data = {
        "name": "New Source",
        "title": "New Title",
        "source_type": "API",
        "parameters.base_url": "http://new.com",
        "parameters.api_key": "key",
    }

    # Mock create response
    new_source = {
        "id": 2,
        "name": "New Source",
        "title": "New Title",
        "type": "API",
        "parameters": {"base_url": "http://new.com", "api_key": "key"},
    }
    mock_data_source_client.create.return_value = new_source

    # We need to iterate over the async generator
    with patch(
        "mindweaver_fe.states.data_sources_state.data_source_client",
        mock_data_source_client,
    ):
        async for _ in state.handle_submit(form_data):
            pass

    assert len(state.all_sources) == 1
    assert state.all_sources[0] == new_source
    mock_data_source_client.create.assert_called_once()


@pytest.mark.asyncio
async def test_handle_submit_update(mock_data_source_client, mock_project_state):
    state = DataSourcesState()
    existing_source = {
        "id": 1,
        "uuid": "uuid-123",
        "name": "Old Name",
        "title": "Old Title",
        "type": "API",
        "parameters": {"base_url": "http://old.com"},
        "created": "",
        "modified": "",
        "status": "Connected",
        "last_sync": "",
    }
    state.all_sources = [existing_source]
    state.open_edit_modal(existing_source)

    # Mock get_state for ProjectState
    async def mock_get_state(state_class):
        from mindweaver_fe.states.project_state import ProjectState

        if state_class == ProjectState:
            return mock_project_state
        return MagicMock()

    object.__setattr__(state, "get_state", mock_get_state)

    form_data = {
        "name": "Updated Name",
        "title": "Updated Title",
        "source_type": "API",
        "parameters.base_url": "http://updated.com",
    }

    # Mock update response
    updated_source = existing_source.copy()
    updated_source["name"] = "Updated Name"
    updated_source["parameters"] = {"base_url": "http://updated.com"}
    mock_data_source_client.update.return_value = updated_source

    with patch(
        "mindweaver_fe.states.data_sources_state.data_source_client",
        mock_data_source_client,
    ):
        async for _ in state.handle_submit(form_data):
            pass

    assert state.all_sources[0]["name"] == "Updated Name"
    mock_data_source_client.update.assert_called_once()


@pytest.mark.asyncio
async def test_handle_test_connection(mock_data_source_client, mock_project_state):
    state = DataSourcesState()
    state.submit_action = "test"
    state.form_data["source_type"] = "API"

    # Mock get_state for ProjectState
    async def mock_get_state(state_class):
        from mindweaver_fe.states.project_state import ProjectState

        if state_class == ProjectState:
            return mock_project_state
        return MagicMock()

    object.__setattr__(state, "get_state", mock_get_state)

    form_data = {"parameters.base_url": "http://test.com"}

    mock_data_source_client.test_connection.return_value = {
        "status": "success",
        "message": "Connected",
    }

    with patch(
        "mindweaver_fe.states.data_sources_state.data_source_client",
        mock_data_source_client,
    ):
        async for result in state.handle_submit(form_data):
            # We expect a toast
            assert isinstance(result, rx.event.EventSpec)

    mock_data_source_client.test_connection.assert_called_once()


@pytest.mark.asyncio
async def test_confirm_delete(mock_data_source_client, mock_project_state):
    state = DataSourcesState()
    source_to_delete = {
        "id": 1,
        "uuid": "uuid-123",
        "name": "To Delete",
        "title": "Title",
        "type": "API",
        "parameters": {},
        "created": "",
        "modified": "",
        "status": "Disconnected",
        "last_sync": "",
    }
    state.all_sources = [source_to_delete]
    state.open_delete_dialog(source_to_delete)

    # Mock get_state for ProjectState
    async def mock_get_state(state_class):
        from mindweaver_fe.states.project_state import ProjectState

        if state_class == ProjectState:
            return mock_project_state
        return MagicMock()

    object.__setattr__(state, "get_state", mock_get_state)

    mock_data_source_client.delete.return_value = True

    with patch(
        "mindweaver_fe.states.data_sources_state.data_source_client",
        mock_data_source_client,
    ):
        await state.confirm_delete()

    assert len(state.all_sources) == 0
    # The delete call now includes headers parameter
    assert mock_data_source_client.delete.call_count == 1
    call_args = mock_data_source_client.delete.call_args
    assert call_args[0][0] == 1  # First positional arg is the ID
