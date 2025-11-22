import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from mindweaver_fe.states.knowledge_db_state import KnowledgeDBState


@pytest.mark.asyncio
async def test_load_databases(mock_knowledge_db_client):
    state = KnowledgeDBState()

    # Mock api client response
    mock_dbs = [{"id": 1, "name": "Test DB", "type": "Vector"}]
    mock_knowledge_db_client.list_all.return_value = mock_dbs

    with patch(
        "mindweaver_fe.states.knowledge_db_state.knowledge_db_client",
        mock_knowledge_db_client,
    ):
        await state.load_databases()

    assert state.all_databases == mock_dbs
    assert state.is_loading is False
    assert state.error_message == ""

    mock_knowledge_db_client.list_all.assert_called_once()


def test_open_create_modal():
    state = KnowledgeDBState()
    state.open_create_modal()

    assert state.show_db_modal is True
    assert state.is_editing is False
    assert state.form_data["name"] == ""
    assert state.form_data["type"] == "Vector"
    assert state.form_errors == {}


def test_open_edit_modal():
    state = KnowledgeDBState()
    db = {
        "id": 1,
        "uuid": "uuid-123",
        "name": "Test DB",
        "title": "Test Title",
        "description": "Desc",
        "type": "Vector",
        "parameters": {},
        "created": "",
        "modified": "",
        "entry_count": 10,
    }

    state.open_edit_modal(db)

    assert state.show_db_modal is True
    assert state.is_editing is True
    assert state.db_to_edit["id"] == 1
    assert state.form_data["name"] == "Test DB"
    assert state.form_data["type"] == "Vector"


@pytest.mark.asyncio
async def test_handle_submit_create(mock_knowledge_db_client):
    state = KnowledgeDBState()
    state.open_create_modal()

    form_data = {
        "name": "New DB",
        "title": "New Title",
        "description": "New Desc",
        "type": "Vector",
    }

    # Mock create response
    new_db = {"id": 2, "name": "New DB", "title": "New Title", "type": "Vector"}
    mock_knowledge_db_client.create.return_value = new_db

    with patch(
        "mindweaver_fe.states.knowledge_db_state.knowledge_db_client",
        mock_knowledge_db_client,
    ):
        await state.handle_submit(form_data)

    assert len(state.all_databases) == 1
    assert state.all_databases[0] == new_db
    mock_knowledge_db_client.create.assert_called_once()


@pytest.mark.asyncio
async def test_handle_submit_update(mock_knowledge_db_client):
    state = KnowledgeDBState()
    existing_db = {
        "id": 1,
        "uuid": "uuid-123",
        "name": "Old Name",
        "title": "Old Title",
        "description": "Desc",
        "type": "Vector",
        "parameters": {},
        "created": "",
        "modified": "",
        "entry_count": 0,
    }
    state.all_databases = [existing_db]
    state.open_edit_modal(existing_db)

    form_data = {
        "name": "Updated Name",
        "title": "Updated Title",
        "description": "Desc",
        "type": "Vector",
    }

    # Mock update response
    updated_db = existing_db.copy()
    updated_db["name"] = "Updated Name"
    updated_db["title"] = "Updated Title"
    mock_knowledge_db_client.update.return_value = updated_db

    with patch(
        "mindweaver_fe.states.knowledge_db_state.knowledge_db_client",
        mock_knowledge_db_client,
    ):
        await state.handle_submit(form_data)

    assert state.all_databases[0]["name"] == "Updated Name"
    mock_knowledge_db_client.update.assert_called_once()


@pytest.mark.asyncio
async def test_confirm_delete(mock_knowledge_db_client):
    state = KnowledgeDBState()
    db_to_delete = {
        "id": 1,
        "uuid": "uuid-123",
        "name": "To Delete",
        "title": "Title",
        "description": "Desc",
        "type": "Vector",
        "parameters": {},
        "created": "",
        "modified": "",
        "entry_count": 0,
    }
    state.all_databases = [db_to_delete]
    state.open_delete_dialog(db_to_delete)

    mock_knowledge_db_client.delete.return_value = True

    with patch(
        "mindweaver_fe.states.knowledge_db_state.knowledge_db_client",
        mock_knowledge_db_client,
    ):
        await state.confirm_delete()

    assert len(state.all_databases) == 0
    mock_knowledge_db_client.delete.assert_called_once_with(1)
