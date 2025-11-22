import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from mindweaver_fe.states.ingestion_state import IngestionState
from mindweaver_fe.states.data_sources_state import DataSourcesState
from mindweaver_fe.states.lakehouse_storage_state import LakehouseStorageState
import reflex as rx


@pytest.mark.asyncio
async def test_load_initial_data(mock_ingestion_client):
    """Test loading ingestions, data sources, and lakehouse storages."""
    state = IngestionState()

    # Mock DataSourcesState
    mock_ds_state = MagicMock(spec=DataSourcesState)
    mock_ds_state.load_initial_data = AsyncMock()
    mock_ds_state.all_sources = [
        {"id": 1, "name": "Test DB", "type": "Database"},
        {"id": 2, "name": "Test API", "type": "API"},
    ]

    # Mock LakehouseStorageState
    mock_ls_state = MagicMock(spec=LakehouseStorageState)
    mock_ls_state.load_initial_data = AsyncMock()
    mock_ls_state.all_storages = [
        {"id": 1, "name": "Test S3", "parameters": {"bucket": "test-bucket"}},
    ]

    # Mock get_state to return our mocked states
    async def mock_get_state(state_class):
        if state_class == DataSourcesState:
            return mock_ds_state
        elif state_class == LakehouseStorageState:
            return mock_ls_state

    object.__setattr__(state, "get_state", mock_get_state)

    # Mock ingestion client response
    mock_ingestions = [
        {
            "id": 1,
            "uuid": "uuid-123",
            "name": "test-ingestion",
            "title": "Test Ingestion",
            "data_source_id": 1,
            "lakehouse_storage_id": 1,
            "storage_path": "/data/test/",
            "cron_schedule": "0 2 * * *",
            "start_date": "",
            "end_date": "",
            "timezone": "UTC",
            "ingestion_type": "full_refresh",
            "config": {"table_name": "test_table", "ingestion_type": "full_refresh"},
            "created": "2025-01-01T00:00:00",
            "modified": "2025-01-01T00:00:00",
        }
    ]
    mock_runs = [
        {
            "id": 1,
            "uuid": "run-uuid-123",
            "ingestion_id": 1,
            "status": "completed",
            "started_at": "2025-01-01T02:00:00",
            "completed_at": "2025-01-01T02:05:00",
            "records_processed": 1000,
            "error_message": "",
            "watermark_metadata": {},
            "created": "2025-01-01T02:00:00",
            "modified": "2025-01-01T02:05:00",
        }
    ]

    mock_ingestion_client.list_all.return_value = mock_ingestions
    mock_ingestion_client.list_runs.return_value = mock_runs

    with patch(
        "mindweaver_fe.states.ingestion_state.ingestion_client",
        mock_ingestion_client,
    ):
        await state.load_initial_data()

    assert state.all_ingestions == mock_ingestions
    assert state.all_data_sources == mock_ds_state.all_sources
    assert state.all_lakehouse_storages == mock_ls_state.all_storages
    assert state.all_runs == mock_runs
    assert state.is_loading is False
    assert state.error_message == ""

    mock_ds_state.load_initial_data.assert_called_once()
    mock_ls_state.load_initial_data.assert_called_once()
    mock_ingestion_client.list_all.assert_called_once()
    mock_ingestion_client.list_runs.assert_called_once_with(1)


def test_open_create_modal():
    """Test opening the create modal with default values."""
    state = IngestionState()
    state.open_create_modal()

    assert state.show_ingestion_modal is True
    assert state.is_editing is False
    assert state.form_data["name"] == ""
    assert state.form_data["title"] == ""
    assert state.form_data["ingestion_type"] == "full_refresh"
    assert state.form_data["config"]["ingestion_type"] == "full_refresh"
    assert state.form_errors == {}
    assert state.error_message == ""


def test_open_create_modal_with_preselected_data_source():
    """Test opening the create modal with a preselected data source."""
    state = IngestionState()
    state.preselected_data_source_id = 5
    state.open_create_modal()

    assert state.form_data["data_source_id"] == 5
    assert state.preselected_data_source_id == 0  # Should be reset


def test_open_edit_modal():
    """Test opening the edit modal with existing ingestion data."""
    state = IngestionState()
    ingestion = {
        "id": 1,
        "uuid": "uuid-123",
        "name": "test-ingestion",
        "title": "Test Ingestion",
        "data_source_id": 1,
        "lakehouse_storage_id": 1,
        "storage_path": "/data/test/",
        "cron_schedule": "0 2 * * *",
        "start_date": "2025-01-01",
        "end_date": "2025-12-31",
        "timezone": "America/New_York",
        "ingestion_type": "incremental",
        "config": {
            "table_name": "orders",
            "ingestion_type": "incremental",
            "primary_keys": ["order_id"],
            "last_modified_column": "updated_at",
            "created_column": "created_at",
            "source_timezone": "America/New_York",
        },
        "created": "2025-01-01T00:00:00",
        "modified": "2025-01-01T00:00:00",
    }

    state.open_edit_modal(ingestion)

    assert state.show_ingestion_modal is True
    assert state.is_editing is True
    assert state.ingestion_to_edit["id"] == 1
    assert state.form_data["name"] == "test-ingestion"
    assert state.form_data["title"] == "Test Ingestion"
    assert state.form_data["ingestion_type"] == "incremental"
    assert state.form_data["config"]["table_name"] == "orders"
    assert state.form_data["config"]["primary_keys"] == ["order_id"]
    assert state.form_errors == {}


def test_close_ingestion_modal():
    """Test closing the ingestion modal."""
    state = IngestionState()
    state.show_ingestion_modal = True
    state.ingestion_to_edit = {"id": 1, "name": "test"}
    state.form_errors = {"name": "Error"}

    state.close_ingestion_modal()

    assert state.show_ingestion_modal is False
    assert state.ingestion_to_edit is None
    assert state.form_errors == {}


def test_set_data_source_id():
    """Test setting data source ID from string."""
    state = IngestionState()
    state.set_data_source_id("5")
    assert state.form_data["data_source_id"] == 5

    state.set_data_source_id("invalid")
    assert state.form_data["data_source_id"] == 0


def test_set_lakehouse_storage_id():
    """Test setting lakehouse storage ID from string."""
    state = IngestionState()
    state.set_lakehouse_storage_id("10")
    assert state.form_data["lakehouse_storage_id"] == 10

    state.set_lakehouse_storage_id("invalid")
    assert state.form_data["lakehouse_storage_id"] == 0


def test_set_config_field():
    """Test setting config field values."""
    state = IngestionState()
    state.set_config_field("table_name", "users")
    assert state.form_data["config"]["table_name"] == "users"

    state.set_config_field("primary_keys", ["id", "email"])
    assert state.form_data["config"]["primary_keys"] == ["id", "email"]


def test_filtered_ingestions():
    """Test filtering ingestions by search query."""
    state = IngestionState()
    state.all_ingestions = [
        {"id": 1, "name": "users-sync", "title": "Users Sync"},
        {"id": 2, "name": "orders-sync", "title": "Orders Sync"},
        {"id": 3, "name": "products-sync", "title": "Products Sync"},
    ]

    state.search_query = "users"
    filtered = state.filtered_ingestions
    assert len(filtered) == 1
    assert filtered[0]["name"] == "users-sync"

    state.search_query = "sync"
    filtered = state.filtered_ingestions
    assert len(filtered) == 3

    state.search_query = "xyz"
    filtered = state.filtered_ingestions
    assert len(filtered) == 0


def test_selected_data_source_type():
    """Test getting the type of selected data source."""
    state = IngestionState()
    state.all_data_sources = [
        {"id": 1, "name": "DB Source", "type": "Database"},
        {"id": 2, "name": "API Source", "type": "API"},
    ]

    state.form_data["data_source_id"] = 1
    assert state.selected_data_source_type == "Database"

    state.form_data["data_source_id"] = 2
    assert state.selected_data_source_type == "API"

    state.form_data["data_source_id"] = 999
    assert state.selected_data_source_type == ""


def test_primary_keys_string():
    """Test converting primary keys list to comma-separated string."""
    state = IngestionState()
    state.form_data["config"]["primary_keys"] = ["id", "email", "username"]
    assert state.primary_keys_string == "id,email,username"

    state.form_data["config"]["primary_keys"] = []
    assert state.primary_keys_string == ""


@pytest.mark.asyncio
async def test_handle_submit_create(mock_ingestion_client):
    """Test creating a new ingestion."""
    state = IngestionState()
    state.open_create_modal()

    form_data = {
        "name": "new-ingestion",
        "title": "New Ingestion",
        "data_source_id": 1,
        "lakehouse_storage_id": 1,
        "storage_path": "/data/new/",
        "cron_schedule": "0 3 * * *",
        "timezone": "UTC",
        "ingestion_type": "full_refresh",
        "config.table_name": "new_table",
        "config.ingestion_type": "full_refresh",
    }

    new_ingestion = {
        "id": 1,
        "uuid": "new-uuid",
        "name": "new-ingestion",
        "title": "New Ingestion",
        "data_source_id": 1,
        "lakehouse_storage_id": 1,
        "storage_path": "/data/new/",
        "cron_schedule": "0 3 * * *",
        "start_date": "",
        "end_date": "",
        "timezone": "UTC",
        "ingestion_type": "full_refresh",
        "config": {"table_name": "new_table", "ingestion_type": "full_refresh"},
        "created": "2025-01-01T00:00:00",
        "modified": "2025-01-01T00:00:00",
    }
    mock_ingestion_client.create.return_value = new_ingestion

    with patch(
        "mindweaver_fe.states.ingestion_state.ingestion_client",
        mock_ingestion_client,
    ):
        async for _ in state.handle_submit(form_data):
            pass

    assert len(state.all_ingestions) == 1
    assert state.all_ingestions[0] == new_ingestion
    mock_ingestion_client.create.assert_called_once()


@pytest.mark.asyncio
async def test_handle_submit_create_validation_errors(mock_ingestion_client):
    """Test validation errors when creating an ingestion."""
    state = IngestionState()
    state.open_create_modal()

    # Test missing name
    form_data = {"name": "", "title": "Test Title"}
    async for _ in state.handle_submit(form_data):
        pass
    assert "name" in state.form_errors
    assert state.form_errors["name"] == "Name is required."

    # Test missing title
    state.form_errors = {}
    form_data = {"name": "test-name", "title": ""}
    async for _ in state.handle_submit(form_data):
        pass
    assert "title" in state.form_errors
    assert state.form_errors["title"] == "Title is required."


@pytest.mark.asyncio
async def test_handle_submit_update(mock_ingestion_client):
    """Test updating an existing ingestion."""
    state = IngestionState()
    existing_ingestion = {
        "id": 1,
        "uuid": "uuid-123",
        "name": "old-name",
        "title": "Old Title",
        "data_source_id": 1,
        "lakehouse_storage_id": 1,
        "storage_path": "/data/old/",
        "cron_schedule": "0 2 * * *",
        "start_date": "",
        "end_date": "",
        "timezone": "UTC",
        "ingestion_type": "full_refresh",
        "config": {"table_name": "old_table", "ingestion_type": "full_refresh"},
        "created": "2025-01-01T00:00:00",
        "modified": "2025-01-01T00:00:00",
    }
    state.all_ingestions = [existing_ingestion]
    state.open_edit_modal(existing_ingestion)

    form_data = {
        "name": "updated-name",
        "title": "Updated Title",
        "data_source_id": 1,
        "lakehouse_storage_id": 1,
        "storage_path": "/data/updated/",
        "cron_schedule": "0 4 * * *",
        "timezone": "UTC",
        "ingestion_type": "full_refresh",
        "config.table_name": "updated_table",
        "config.ingestion_type": "full_refresh",
    }

    updated_ingestion = existing_ingestion.copy()
    updated_ingestion["name"] = "updated-name"
    updated_ingestion["title"] = "Updated Title"
    updated_ingestion["storage_path"] = "/data/updated/"
    updated_ingestion["config"]["table_name"] = "updated_table"
    mock_ingestion_client.update.return_value = updated_ingestion

    with patch(
        "mindweaver_fe.states.ingestion_state.ingestion_client",
        mock_ingestion_client,
    ):
        async for _ in state.handle_submit(form_data):
            pass

    assert state.all_ingestions[0]["name"] == "updated-name"
    assert state.all_ingestions[0]["title"] == "Updated Title"
    mock_ingestion_client.update.assert_called_once()


@pytest.mark.asyncio
async def test_handle_submit_incremental_with_primary_keys(mock_ingestion_client):
    """Test creating an incremental ingestion with primary keys."""
    state = IngestionState()
    state.open_create_modal()

    form_data = {
        "name": "incremental-ingestion",
        "title": "Incremental Ingestion",
        "data_source_id": 1,
        "lakehouse_storage_id": 1,
        "storage_path": "/data/incremental/",
        "cron_schedule": "0 */4 * * *",
        "timezone": "America/New_York",
        "ingestion_type": "incremental",
        "config.table_name": "orders",
        "config.ingestion_type": "incremental",
        "config.primary_keys": "order_id, customer_id",  # Comma-separated
        "config.last_modified_column": "updated_at",
        "config.created_column": "created_at",
        "config.source_timezone": "America/New_York",
    }

    new_ingestion = {
        "id": 1,
        "uuid": "inc-uuid",
        "name": "incremental-ingestion",
        "title": "Incremental Ingestion",
        "data_source_id": 1,
        "lakehouse_storage_id": 1,
        "storage_path": "/data/incremental/",
        "cron_schedule": "0 */4 * * *",
        "start_date": "",
        "end_date": "",
        "timezone": "America/New_York",
        "ingestion_type": "incremental",
        "config": {
            "table_name": "orders",
            "ingestion_type": "incremental",
            "primary_keys": ["order_id", "customer_id"],
            "last_modified_column": "updated_at",
            "created_column": "created_at",
            "source_timezone": "America/New_York",
        },
        "created": "2025-01-01T00:00:00",
        "modified": "2025-01-01T00:00:00",
    }
    mock_ingestion_client.create.return_value = new_ingestion

    with patch(
        "mindweaver_fe.states.ingestion_state.ingestion_client",
        mock_ingestion_client,
    ):
        async for _ in state.handle_submit(form_data):
            pass

    # Verify that primary_keys were correctly parsed from comma-separated string
    call_args = mock_ingestion_client.create.call_args[0][0]
    assert call_args["config"]["primary_keys"] == ["order_id", "customer_id"]


@pytest.mark.asyncio
async def test_confirm_delete(mock_ingestion_client):
    """Test deleting an ingestion."""
    state = IngestionState()
    ingestion_to_delete = {
        "id": 1,
        "uuid": "uuid-123",
        "name": "to-delete",
        "title": "To Delete",
        "data_source_id": 1,
        "lakehouse_storage_id": 1,
        "storage_path": "/data/delete/",
        "cron_schedule": "0 2 * * *",
        "start_date": "",
        "end_date": "",
        "timezone": "UTC",
        "ingestion_type": "full_refresh",
        "config": {},
        "created": "2025-01-01T00:00:00",
        "modified": "2025-01-01T00:00:00",
    }
    state.all_ingestions = [ingestion_to_delete]
    state.open_delete_dialog(ingestion_to_delete)

    mock_ingestion_client.delete.return_value = True

    with patch(
        "mindweaver_fe.states.ingestion_state.ingestion_client",
        mock_ingestion_client,
    ):
        await state.confirm_delete()

    assert len(state.all_ingestions) == 0
    mock_ingestion_client.delete.assert_called_once_with(1)


@pytest.mark.asyncio
async def test_confirm_execute(mock_ingestion_client):
    """Test executing an ingestion."""
    state = IngestionState()
    ingestion_to_execute = {
        "id": 1,
        "uuid": "uuid-123",
        "name": "to-execute",
        "title": "To Execute",
        "data_source_id": 1,
        "lakehouse_storage_id": 1,
        "storage_path": "/data/execute/",
        "cron_schedule": "0 2 * * *",
        "start_date": "",
        "end_date": "",
        "timezone": "UTC",
        "ingestion_type": "full_refresh",
        "config": {},
        "created": "2025-01-01T00:00:00",
        "modified": "2025-01-01T00:00:00",
    }
    state.open_execute_dialog(ingestion_to_execute)

    mock_runs = [
        {
            "id": 1,
            "uuid": "run-uuid",
            "ingestion_id": 1,
            "status": "running",
            "started_at": "2025-01-01T02:00:00",
            "completed_at": "",
            "records_processed": 0,
            "error_message": "",
            "watermark_metadata": {},
            "created": "2025-01-01T02:00:00",
            "modified": "2025-01-01T02:00:00",
        }
    ]

    mock_ingestion_client.execute_ingestion.return_value = {"status": "success"}
    mock_ingestion_client.list_runs.return_value = mock_runs

    with patch(
        "mindweaver_fe.states.ingestion_state.ingestion_client",
        mock_ingestion_client,
    ):
        async for _ in state.confirm_execute():
            pass

    assert len(state.all_runs) == 1
    assert state.all_runs[0]["status"] == "running"
    mock_ingestion_client.execute_ingestion.assert_called_once_with(1)
    mock_ingestion_client.list_runs.assert_called_once_with(1)


def test_open_delete_dialog():
    """Test opening the delete confirmation dialog."""
    state = IngestionState()
    ingestion = {
        "id": 1,
        "uuid": "uuid-123",
        "name": "test",
        "title": "Test",
        "data_source_id": 1,
        "lakehouse_storage_id": 1,
        "storage_path": "/data/test/",
        "cron_schedule": "0 2 * * *",
        "start_date": "",
        "end_date": "",
        "timezone": "UTC",
        "ingestion_type": "full_refresh",
        "config": {},
        "created": "2025-01-01T00:00:00",
        "modified": "2025-01-01T00:00:00",
    }

    state.open_delete_dialog(ingestion)

    assert state.show_delete_dialog is True
    assert state.ingestion_to_delete["id"] == 1


def test_close_delete_dialog():
    """Test closing the delete confirmation dialog."""
    state = IngestionState()
    state.show_delete_dialog = True
    state.ingestion_to_delete = {"id": 1}

    state.close_delete_dialog()

    assert state.show_delete_dialog is False
    assert state.ingestion_to_delete is None


def test_open_execute_dialog():
    """Test opening the execute confirmation dialog."""
    state = IngestionState()
    ingestion = {
        "id": 1,
        "uuid": "uuid-123",
        "name": "test",
        "title": "Test",
        "data_source_id": 1,
        "lakehouse_storage_id": 1,
        "storage_path": "/data/test/",
        "cron_schedule": "0 2 * * *",
        "start_date": "",
        "end_date": "",
        "timezone": "UTC",
        "ingestion_type": "full_refresh",
        "config": {},
        "created": "2025-01-01T00:00:00",
        "modified": "2025-01-01T00:00:00",
    }

    state.open_execute_dialog(ingestion)

    assert state.show_execute_dialog is True
    assert state.ingestion_to_execute["id"] == 1


def test_close_execute_dialog():
    """Test closing the execute confirmation dialog."""
    state = IngestionState()
    state.show_execute_dialog = True
    state.ingestion_to_execute = {"id": 1}

    state.close_execute_dialog()

    assert state.show_execute_dialog is False
    assert state.ingestion_to_execute is None
