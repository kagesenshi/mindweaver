import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from mindweaver_fe.states.ai_agents_state import AIAgentsState
from mindweaver_fe.states.knowledge_db_state import KnowledgeDBState


@pytest.mark.asyncio
async def test_load_agents(mock_ai_agent_client, mock_project_state):
    # Mock the state
    state = AIAgentsState()

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
    mock_agents = [{"id": 1, "name": "Test Agent", "status": "Active"}]
    mock_ai_agent_client.list_all.return_value = mock_agents

    # Run the event handler
    with patch(
        "mindweaver_fe.states.ai_agents_state.ai_agent_client", mock_ai_agent_client
    ):
        await state.load_agents()

    # Verify results
    assert state.all_agents == mock_agents
    assert state.all_knowledge_dbs == [{"id": 1, "name": "Test DB"}]
    assert state.is_loading is False
    assert state.error_message == ""

    # Verify calls
    mock_kdb_state.load_databases.assert_called_once()
    mock_ai_agent_client.list_all.assert_called_once()


def test_open_create_modal():
    state = AIAgentsState()
    state.open_create_modal()

    assert state.show_agent_modal is True
    assert state.is_editing is False
    assert state.form_data["name"] == ""
    assert state.form_data["model"] == "gpt-4-turbo"
    assert state.form_errors == {}


def test_open_edit_modal():
    state = AIAgentsState()
    agent = {
        "id": 1,
        "uuid": "uuid-123",
        "name": "Test Agent",
        "title": "Test Title",
        "model": "gpt-4-turbo",
        "temperature": 0.7,
        "system_prompt": "Prompt",
        "status": "Active",
        "knowledge_db_ids": ["1"],
        "created": "2023-01-01",
        "modified": "2023-01-01",
    }

    state.open_edit_modal(agent)

    assert state.show_agent_modal is True
    assert state.is_editing is True
    assert state.agent_to_edit["id"] == 1
    assert state.form_data["name"] == "Test Agent"
    assert state.form_data["knowledge_db_ids"] == ["1"]


@pytest.mark.asyncio
async def test_handle_submit_create(mock_ai_agent_client, mock_project_state):
    state = AIAgentsState()
    state.open_create_modal()

    # Mock get_state for ProjectState
    async def mock_get_state(state_class):
        from mindweaver_fe.states.project_state import ProjectState

        if state_class == ProjectState:
            return mock_project_state
        return MagicMock()

    object.__setattr__(state, "get_state", mock_get_state)

    form_data = {
        "name": "New Agent",
        "title": "New Title",
        "system_prompt": "New Prompt",
    }

    # Mock create response
    new_agent = {
        "id": 2,
        "name": "New Agent",
        "title": "New Title",
        "status": "Inactive",
        "knowledge_db_ids": [],
    }
    mock_ai_agent_client.create.return_value = new_agent

    with patch(
        "mindweaver_fe.states.ai_agents_state.ai_agent_client", mock_ai_agent_client
    ):
        await state.handle_submit(form_data)

    assert len(state.all_agents) == 1
    assert state.all_agents[0] == new_agent
    mock_ai_agent_client.create.assert_called_once()


@pytest.mark.asyncio
async def test_handle_submit_update(mock_ai_agent_client, mock_project_state):
    state = AIAgentsState()
    existing_agent = {
        "id": 1,
        "uuid": "uuid-123",
        "name": "Old Name",
        "title": "Old Title",
        "model": "gpt-4-turbo",
        "temperature": 0.7,
        "system_prompt": "Prompt",
        "status": "Active",
        "knowledge_db_ids": [],
        "created": "",
        "modified": "",
    }
    state.all_agents = [existing_agent]
    state.open_edit_modal(existing_agent)

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
        "system_prompt": "Prompt",
    }

    # Mock update response
    updated_agent = existing_agent.copy()
    updated_agent["name"] = "Updated Name"
    updated_agent["title"] = "Updated Title"
    mock_ai_agent_client.update.return_value = updated_agent

    with patch(
        "mindweaver_fe.states.ai_agents_state.ai_agent_client", mock_ai_agent_client
    ):
        await state.handle_submit(form_data)

    assert state.all_agents[0]["name"] == "Updated Name"
    mock_ai_agent_client.update.assert_called_once()


@pytest.mark.asyncio
async def test_confirm_delete(mock_ai_agent_client, mock_project_state):
    state = AIAgentsState()
    agent_to_delete = {
        "id": 1,
        "uuid": "uuid-123",
        "name": "To Delete",
        "title": "Title",
        "model": "gpt-4-turbo",
        "temperature": 0.7,
        "system_prompt": "Prompt",
        "status": "Inactive",
        "knowledge_db_ids": [],
        "created": "",
        "modified": "",
    }
    state.all_agents = [agent_to_delete]
    state.open_delete_dialog(agent_to_delete)

    # Mock get_state for ProjectState
    async def mock_get_state(state_class):
        from mindweaver_fe.states.project_state import ProjectState

        if state_class == ProjectState:
            return mock_project_state
        return MagicMock()

    object.__setattr__(state, "get_state", mock_get_state)

    mock_ai_agent_client.delete.return_value = True

    with patch(
        "mindweaver_fe.states.ai_agents_state.ai_agent_client", mock_ai_agent_client
    ):
        await state.confirm_delete()

    assert len(state.all_agents) == 0
    # The delete call now includes headers parameter
    assert mock_ai_agent_client.delete.call_count == 1
    call_args = mock_ai_agent_client.delete.call_args
    assert call_args[0][0] == 1  # First positional arg is the ID
