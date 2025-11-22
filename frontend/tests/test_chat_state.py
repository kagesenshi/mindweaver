import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from mindweaver_fe.states.chat_state import ChatState
from mindweaver_fe.states.ai_agents_state import AIAgentsState
from mindweaver_fe.states.knowledge_db_state import KnowledgeDBState
import reflex as rx


@pytest.mark.asyncio
async def test_load_initial_data(mock_chat_client, mock_project_state):
    state = ChatState()

    # Mock get_state for AIAgentsState, KnowledgeDBState, and ProjectState
    mock_agent_state = MagicMock(spec=AIAgentsState)
    mock_agent_state.load_agents = AsyncMock()
    mock_agent_state.all_agents = [{"id": 1, "name": "Test Agent"}]

    mock_kdb_state = MagicMock(spec=KnowledgeDBState)
    mock_kdb_state.load_databases = AsyncMock()
    mock_kdb_state.all_databases = [{"id": 1, "name": "Test DB"}]

    async def mock_get_state(state_cls):
        if state_cls == AIAgentsState:
            return mock_agent_state
        elif state_cls == KnowledgeDBState:
            return mock_kdb_state
        from mindweaver_fe.states.project_state import ProjectState

        if state_cls == ProjectState:
            return mock_project_state
        return None

    object.__setattr__(state, "get_state", AsyncMock(side_effect=mock_get_state))

    # Mock api client response
    mock_chats = [{"id": 1, "name": "Test Chat", "messages": []}]
    mock_chat_client.list_all.return_value = mock_chats

    with patch("mindweaver_fe.states.chat_state.chat_client", mock_chat_client):
        await state.load_initial_data()

    assert state.all_agents == [{"id": 1, "name": "Test Agent"}]
    assert state.all_dbs == [{"id": 1, "name": "Test DB"}]
    assert state.all_chats == mock_chats
    assert state.is_loading is False
    assert state.error_message == ""

    mock_agent_state.load_agents.assert_called_once()
    mock_kdb_state.load_databases.assert_called_once()
    mock_chat_client.list_all.assert_called_once()


@pytest.mark.asyncio
async def test_create_new_conversation(mock_chat_client, mock_project_state):
    state = ChatState()
    state.selected_agent_id = "1"

    # Mock get_state for ProjectState
    async def mock_get_state(state_class):
        from mindweaver_fe.states.project_state import ProjectState

        if state_class == ProjectState:
            return mock_project_state
        return MagicMock()

    object.__setattr__(state, "get_state", mock_get_state)

    # Mock create response
    new_chat = {
        "id": 2,
        "name": "New Chat",
        "title": "Conversation 1",
        "messages": [],
        "agent_id": "1",
    }
    mock_chat_client.create.return_value = new_chat

    with patch("mindweaver_fe.states.chat_state.chat_client", mock_chat_client):
        await state.create_new_conversation()

    assert len(state.all_chats) == 1
    assert state.all_chats[0] == new_chat
    assert state.current_conversation_id == 2
    mock_chat_client.create.assert_called_once()


@pytest.mark.asyncio
async def test_handle_send_message(mock_chat_client, mock_project_state):
    state = ChatState()
    state.current_conversation_id = 1
    state.selected_agent_id = "1"
    state.all_agents = [{"id": 1, "name": "Test Agent"}]

    current_chat = {"id": 1, "name": "Test Chat", "messages": [], "agent_id": "1"}
    state.all_chats = [current_chat]

    # Mock get_state for ProjectState
    async def mock_get_state(state_class):
        from mindweaver_fe.states.project_state import ProjectState

        if state_class == ProjectState:
            return mock_project_state
        return MagicMock()

    object.__setattr__(state, "get_state", mock_get_state)

    form_data = {"input_message": "Hello"}

    # Mock update response
    updated_chat = current_chat.copy()
    updated_chat["messages"] = [
        {"role": "user", "content": "Hello", "timestamp": "10:00"},
        {"role": "assistant", "content": "Response", "timestamp": "10:00"},
    ]
    mock_chat_client.update.return_value = updated_chat

    with patch("mindweaver_fe.states.chat_state.chat_client", mock_chat_client):
        async for _ in state.handle_send_message(form_data):
            pass

    # Verify that messages were added (checking the final state after streaming)
    # Note: The streaming logic modifies all_chats in place
    assert len(state.all_chats[0]["messages"]) == 2
    assert state.all_chats[0]["messages"][0]["content"] == "Hello"
    assert state.all_chats[0]["messages"][1]["role"] == "assistant"

    mock_chat_client.update.assert_called_once()
