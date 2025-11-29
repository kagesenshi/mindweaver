import reflex as rx
from typing import TypedDict, Optional, Any
import uuid
import datetime
import asyncio
import logging
from mindweaver_fe.api_client import ingestion_client
from mindweaver_fe.states.data_sources_state import DataSource, DataSourcesState
from mindweaver_fe.states.lakehouse_storage_state import (
    LakehouseStorage,
    LakehouseStorageState,
)
from mindweaver_fe.states.project_state import ProjectState
import httpx


# TypedDict models
class DatabaseIngestionConfig(TypedDict):
    table_name: str
    ingestion_type: str  # "full_refresh" or "incremental"
    primary_keys: list[str]
    last_modified_column: str
    created_column: str
    source_timezone: str


class IngestionFormData(TypedDict):
    name: str
    title: str
    data_source_id: int
    lakehouse_storage_id: int
    storage_path: str
    cron_schedule: str
    start_date: str
    end_date: str
    timezone: str
    ingestion_type: str
    config: dict[str, Any]


class Ingestion(TypedDict):
    id: int
    uuid: str
    name: str
    title: str
    data_source_id: int
    lakehouse_storage_id: int
    storage_path: str
    cron_schedule: str
    start_date: str
    end_date: str
    timezone: str
    ingestion_type: str
    config: dict[str, Any]
    created: str
    modified: str


class IngestionRun(TypedDict):
    id: int
    uuid: str
    ingestion_id: int
    status: str  # "pending", "running", "completed", "failed"
    started_at: str
    completed_at: str
    records_processed: int
    error_message: str
    watermark_metadata: dict[str, Any]
    created: str
    modified: str


class IngestionState(rx.State):
    """Manages the state for the ingestion page."""

    all_ingestions: list[Ingestion] = []
    all_runs: list[IngestionRun] = []
    all_data_sources: list[DataSource] = []
    all_lakehouse_storages: list[LakehouseStorage] = []
    show_ingestion_modal: bool = False
    show_delete_dialog: bool = False
    show_execute_dialog: bool = False
    is_editing: bool = False
    ingestion_to_edit: Ingestion | None = None
    ingestion_to_delete: Ingestion | None = None
    ingestion_to_execute: Ingestion | None = None
    form_data: IngestionFormData = {
        "name": "",
        "title": "",
        "data_source_id": 0,
        "lakehouse_storage_id": 0,
        "storage_path": "",
        "cron_schedule": "0 2 * * *",
        "start_date": "",
        "end_date": "",
        "timezone": "UTC",
        "ingestion_type": "full_refresh",
        "config": {
            "table_name": "",
            "ingestion_type": "full_refresh",
            "primary_keys": [],
            "last_modified_column": "",
            "created_column": "",
            "source_timezone": "UTC",
        },
    }
    form_errors: dict = {}
    search_query: str = ""
    is_loading: bool = False
    is_executing: bool = False
    error_message: str = ""

    # For pre-filling from data sources page
    preselected_data_source_id: int = 0

    def _get_default_form_data(self) -> IngestionFormData:
        return {
            "name": "",
            "title": "",
            "data_source_id": 0,
            "lakehouse_storage_id": 0,
            "storage_path": "",
            "cron_schedule": "0 2 * * *",
            "start_date": "",
            "end_date": "",
            "timezone": "UTC",
            "ingestion_type": "full_refresh",
            "config": {
                "table_name": "",
                "ingestion_type": "full_refresh",
                "primary_keys": [],
                "last_modified_column": "",
                "created_column": "",
                "source_timezone": "UTC",
            },
        }

    @rx.event
    async def set_search_query(self, value):
        self.search_query = value

    async def _get_headers(self) -> dict[str, str]:
        project_state = await self.get_state(ProjectState)
        if project_state.current_project:
            return {"X-Project-ID": str(project_state.current_project["id"])}
        return {}

    @rx.event
    async def load_initial_data(self):
        """Load ingestions, data sources, and lakehouse storages from API."""
        self.is_loading = True
        self.error_message = ""
        try:
            # Load data sources
            ds_state = await self.get_state(DataSourcesState)
            await ds_state.load_initial_data()
            self.all_data_sources = ds_state.all_sources

            # Load lakehouse storages
            ls_state = await self.get_state(LakehouseStorageState)
            await ls_state.load_initial_data()
            self.all_lakehouse_storages = ls_state.all_storages

            # Load ingestions
            headers = await self._get_headers()
            ingestions = await ingestion_client.list_all(headers=headers)
            self.all_ingestions = ingestions

            # Load all runs
            all_runs = []
            for ingestion in ingestions:
                runs = await ingestion_client.list_runs(
                    ingestion["id"], headers=headers
                )
                all_runs.extend(runs)
            self.all_runs = all_runs

        except Exception as e:
            self.error_message = f"Failed to load data: {str(e)}"
        finally:
            self.is_loading = False

    @rx.var
    def filtered_ingestions(self) -> list[Ingestion]:
        return [
            ingestion
            for ingestion in self.all_ingestions
            if self.search_query.lower() in ingestion.get("name", "").lower()
        ]

    @rx.var
    def data_source_names(self) -> dict[int, str]:
        return {ds["id"]: ds.get("name", "") for ds in self.all_data_sources}

    @rx.var
    def lakehouse_storage_names(self) -> dict[int, str]:
        return {ls["id"]: ls.get("name", "") for ls in self.all_lakehouse_storages}

    @rx.var
    def ingestion_names(self) -> dict[int, str]:
        return {ing["id"]: ing.get("name", "") for ing in self.all_ingestions}

    @rx.var
    def selected_data_source_type(self) -> str:
        """Get the type of the currently selected data source."""
        ds_id = self.form_data.get("data_source_id", 0)
        for ds in self.all_data_sources:
            if ds["id"] == ds_id:
                return ds.get("type", "")
        return ""

    @rx.var
    def primary_keys_string(self) -> str:
        """Get primary keys as comma-separated string."""
        keys = self.form_data.get("config", {}).get("primary_keys", [])
        if isinstance(keys, list):
            return ",".join(keys)
        return ""

    @rx.event
    def open_create_modal(self):
        self.is_editing = False
        self.form_data = self._get_default_form_data()

        # Pre-fill data source if coming from data sources page
        if self.preselected_data_source_id > 0:
            self.form_data["data_source_id"] = self.preselected_data_source_id
            self.preselected_data_source_id = 0  # Reset after use

        self.form_errors = {}
        self.error_message = ""
        self.show_ingestion_modal = True

    @rx.event
    def open_edit_modal(self, ingestion: Ingestion):
        self.is_editing = True
        typed_ingestion: Ingestion = {
            "id": ingestion.get("id", 0),
            "uuid": ingestion.get("uuid", ""),
            "name": ingestion.get("name", ""),
            "title": ingestion.get("title", ""),
            "data_source_id": ingestion.get("data_source_id", 0),
            "lakehouse_storage_id": ingestion.get("lakehouse_storage_id", 0),
            "storage_path": ingestion.get("storage_path", ""),
            "cron_schedule": ingestion.get("cron_schedule", "0 2 * * *"),
            "start_date": ingestion.get("start_date", ""),
            "end_date": ingestion.get("end_date", ""),
            "timezone": ingestion.get("timezone", "UTC"),
            "ingestion_type": ingestion.get("ingestion_type", "full_refresh"),
            "config": ingestion.get("config", {}),
            "created": ingestion.get("created", ""),
            "modified": ingestion.get("modified", ""),
        }
        self.ingestion_to_edit = typed_ingestion
        self.form_data = self._get_default_form_data()
        self.form_data["name"] = typed_ingestion["name"]
        self.form_data["title"] = typed_ingestion["title"]
        self.form_data["data_source_id"] = typed_ingestion["data_source_id"]
        self.form_data["lakehouse_storage_id"] = typed_ingestion["lakehouse_storage_id"]
        self.form_data["storage_path"] = typed_ingestion["storage_path"]
        self.form_data["cron_schedule"] = typed_ingestion["cron_schedule"]
        self.form_data["start_date"] = typed_ingestion["start_date"]
        self.form_data["end_date"] = typed_ingestion["end_date"]
        self.form_data["timezone"] = typed_ingestion["timezone"]
        self.form_data["ingestion_type"] = typed_ingestion["ingestion_type"]
        self.form_data["config"] = typed_ingestion["config"]
        self.form_errors = {}
        self.error_message = ""
        self.show_ingestion_modal = True

    @rx.event
    def close_ingestion_modal(self):
        self.show_ingestion_modal = False
        self.ingestion_to_edit = None
        self.form_errors = {}

    @rx.event
    def set_form_data_field(self, field: str, value: Any):
        self.form_data[field] = value

    @rx.event
    def set_data_source_id(self, value: str):
        """Set data source ID from string value."""
        try:
            self.form_data["data_source_id"] = int(value)
        except (ValueError, TypeError):
            self.form_data["data_source_id"] = 0

    @rx.event
    def set_lakehouse_storage_id(self, value: str):
        """Set lakehouse storage ID from string value."""
        try:
            self.form_data["lakehouse_storage_id"] = int(value)
        except (ValueError, TypeError):
            self.form_data["lakehouse_storage_id"] = 0

    @rx.event
    def set_config_field(self, field: str, value: Any):
        self.form_data["config"][field] = value

    @rx.event
    async def handle_submit(self, form_data: dict):
        # Clear previous errors
        self.form_errors = {}
        self.error_message = ""

        submitted_name = form_data.get("name", "")
        submitted_title = form_data.get("title", "")

        # Validate required fields
        if not submitted_name.strip():
            self.form_errors = {"name": "Name is required."}
            return
        if not submitted_title.strip():
            self.form_errors = {"title": "Title is required."}
            return

        # Build config from form data
        config = {}
        for k, v in form_data.items():
            if k.startswith("config."):
                key = k.split(".", 1)[1]
                if key == "primary_keys":
                    # Split comma-separated values
                    config[key] = [pk.strip() for pk in v.split(",") if pk.strip()]
                else:
                    config[key] = v

        current_form_data = self.form_data.copy()
        current_form_data["name"] = submitted_name
        current_form_data["title"] = submitted_title

        # Update scalar fields from form
        for field in [
            "data_source_id",
            "lakehouse_storage_id",
            "storage_path",
            "cron_schedule",
            "start_date",
            "end_date",
            "timezone",
            "ingestion_type",
        ]:
            if field in form_data:
                current_form_data[field] = form_data[field]

        current_form_data["config"] = {
            **current_form_data["config"],
            **config,
        }

        try:
            api_data = {
                "name": current_form_data["name"],
                "title": current_form_data["title"],
                "data_source_id": int(current_form_data["data_source_id"]),
                "lakehouse_storage_id": int(current_form_data["lakehouse_storage_id"]),
                "storage_path": current_form_data["storage_path"],
                "cron_schedule": current_form_data["cron_schedule"],
                "start_date": current_form_data["start_date"] or None,
                "end_date": current_form_data["end_date"] or None,
                "timezone": current_form_data["timezone"],
                "ingestion_type": current_form_data["ingestion_type"],
                "config": current_form_data["config"],
            }

            headers = await self._get_headers()

            if self.is_editing and self.ingestion_to_edit:
                updated_ingestion = await ingestion_client.update(
                    self.ingestion_to_edit["id"], api_data, headers=headers
                )
                for i, ing in enumerate(self.all_ingestions):
                    if ing["id"] == self.ingestion_to_edit["id"]:
                        self.all_ingestions[i] = updated_ingestion
                        break
            else:
                new_ingestion = await ingestion_client.create(api_data, headers=headers)
                self.all_ingestions.append(new_ingestion)

            yield IngestionState.close_ingestion_modal
        except httpx.HTTPStatusError as e:
            # Extract validation errors from the response
            try:
                error_data = e.response.json()
                if "detail" in error_data and isinstance(error_data["detail"], list):
                    # Parse validation errors
                    for error in error_data["detail"]:
                        if "loc" in error and len(error["loc"]) > 1:
                            field_name = error["loc"][-1]  # Get the field name
                            error_msg = error.get("msg", "Invalid value")
                            self.form_errors[field_name] = error_msg
                    # If we have field errors, don't set general error message
                    if not self.form_errors:
                        self.error_message = (
                            f"Failed to save ingestion: {str(error_data)}"
                        )
                else:
                    self.error_message = f"Failed to save ingestion: {str(error_data)}"
            except Exception:
                self.error_message = f"Failed to save ingestion: {str(e)}"
        except Exception as e:
            self.error_message = f"Failed to save ingestion: {str(e)}"

    @rx.event
    def open_delete_dialog(self, ingestion: Ingestion):
        typed_ingestion: Ingestion = {
            "id": ingestion.get("id", 0),
            "uuid": ingestion.get("uuid", ""),
            "name": ingestion.get("name", ""),
            "title": ingestion.get("title", ""),
            "data_source_id": ingestion.get("data_source_id", 0),
            "lakehouse_storage_id": ingestion.get("lakehouse_storage_id", 0),
            "storage_path": ingestion.get("storage_path", ""),
            "cron_schedule": ingestion.get("cron_schedule", ""),
            "start_date": ingestion.get("start_date", ""),
            "end_date": ingestion.get("end_date", ""),
            "timezone": ingestion.get("timezone", "UTC"),
            "ingestion_type": ingestion.get("ingestion_type", "full_refresh"),
            "config": ingestion.get("config", {}),
            "created": ingestion.get("created", ""),
            "modified": ingestion.get("modified", ""),
        }
        self.ingestion_to_delete = typed_ingestion
        self.show_delete_dialog = True

    @rx.event
    def close_delete_dialog(self):
        self.show_delete_dialog = False
        self.ingestion_to_delete = None

    @rx.event
    async def confirm_delete(self):
        if not self.ingestion_to_delete:
            return IngestionState.close_delete_dialog

        self.error_message = ""
        try:
            headers = await self._get_headers()
            await ingestion_client.delete(
                self.ingestion_to_delete["id"], headers=headers
            )
            self.all_ingestions = [
                ing
                for ing in self.all_ingestions
                if ing["id"] != self.ingestion_to_delete["id"]
            ]
        except httpx.HTTPStatusError as e:
            try:
                error_data = e.response.json()
                self.error_message = (
                    f"Failed to delete ingestion: {error_data.get('detail', str(e))}"
                )
            except Exception:
                self.error_message = f"Failed to delete ingestion: {str(e)}"
        except Exception as e:
            self.error_message = f"Failed to delete ingestion: {str(e)}"

        return IngestionState.close_delete_dialog

    @rx.event
    def open_execute_dialog(self, ingestion: Ingestion):
        typed_ingestion: Ingestion = {
            "id": ingestion.get("id", 0),
            "uuid": ingestion.get("uuid", ""),
            "name": ingestion.get("name", ""),
            "title": ingestion.get("title", ""),
            "data_source_id": ingestion.get("data_source_id", 0),
            "lakehouse_storage_id": ingestion.get("lakehouse_storage_id", 0),
            "storage_path": ingestion.get("storage_path", ""),
            "cron_schedule": ingestion.get("cron_schedule", ""),
            "start_date": ingestion.get("start_date", ""),
            "end_date": ingestion.get("end_date", ""),
            "timezone": ingestion.get("timezone", "UTC"),
            "ingestion_type": ingestion.get("ingestion_type", "full_refresh"),
            "config": ingestion.get("config", {}),
            "created": ingestion.get("created", ""),
            "modified": ingestion.get("modified", ""),
        }
        self.ingestion_to_execute = typed_ingestion
        self.show_execute_dialog = True

    @rx.event
    def close_execute_dialog(self):
        self.show_execute_dialog = False
        self.ingestion_to_execute = None

    @rx.event
    async def confirm_execute(self):
        if not self.ingestion_to_execute:
            yield IngestionState.close_execute_dialog

        self.is_executing = True
        self.error_message = ""
        try:
            headers = await self._get_headers()
            result = await ingestion_client.execute_ingestion(
                self.ingestion_to_execute["id"], headers=headers
            )
            # Reload runs
            runs = await ingestion_client.list_runs(
                self.ingestion_to_execute["id"], headers=headers
            )
            # Update all_runs
            self.all_runs = [
                r
                for r in self.all_runs
                if r["ingestion_id"] != self.ingestion_to_execute["id"]
            ]
            self.all_runs.extend(runs)
            yield rx.toast.success("Ingestion execution started")
        except Exception as e:
            self.error_message = f"Failed to execute ingestion: {str(e)}"
            yield rx.toast.error("Execution failed")
        finally:
            self.is_executing = False

        yield IngestionState.close_execute_dialog
