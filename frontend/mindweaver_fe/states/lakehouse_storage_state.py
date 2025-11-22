import reflex as rx
from typing import TypedDict, Optional, Any
import uuid
import datetime
import asyncio
import logging
from mindweaver_fe.states.project_state import ProjectState
from mindweaver_fe.api_client import lakehouse_storage_client
import httpx


class S3Config(TypedDict):
    bucket: str
    region: str
    access_key: str
    secret_key: str
    endpoint_url: str


class LakehouseStorageFormData(TypedDict):
    name: str
    title: str
    parameters: S3Config


class LakehouseStorage(TypedDict):
    id: int
    uuid: str
    name: str
    title: str
    parameters: dict[str, Any]
    created: str
    modified: str


class LakehouseStorageState(rx.State):
    """Manages the state for the lakehouse storage page."""

    all_storages: list[LakehouseStorage] = []
    show_storage_modal: bool = False
    show_delete_dialog: bool = False
    is_editing: bool = False
    storage_to_edit: LakehouseStorage | None = None
    storage_to_delete: LakehouseStorage | None = None
    form_data: LakehouseStorageFormData = {
        "name": "",
        "title": "",
        "parameters": {
            "bucket": "",
            "region": "us-east-1",
            "access_key": "",
            "secret_key": "",
            "endpoint_url": "",
        },
    }
    form_errors: dict = {}
    search_query: str = ""
    is_testing_connection: bool = False
    is_loading: bool = False
    error_message: str = ""
    clear_secret_key: bool = False  # Flag to clear secret key in edit mode

    def _get_default_form_data(self) -> LakehouseStorageFormData:
        return {
            "name": "",
            "title": "",
            "parameters": {
                "bucket": "",
                "region": "us-east-1",
                "access_key": "",
                "secret_key": "",
                "endpoint_url": "",
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
        """Load lakehouse storages from API."""
        self.is_loading = True
        self.error_message = ""
        try:
            # Load storages from API
            headers = await self._get_headers()
            storages = await lakehouse_storage_client.list_all(headers=headers)
            self.all_storages = storages
        except Exception as e:
            self.error_message = f"Failed to load data: {str(e)}"
        finally:
            self.is_loading = False

    @rx.var
    def filtered_storages(self) -> list[LakehouseStorage]:
        return [
            storage
            for storage in self.all_storages
            if self.search_query.lower() in storage.get("name", "").lower()
        ]

    @rx.event
    def open_create_modal(self):
        self.is_editing = False
        self.form_data = self._get_default_form_data()
        self.form_errors = {}
        self.error_message = ""
        self.show_storage_modal = True

    @rx.event
    def open_edit_modal(self, storage: LakehouseStorage):
        self.is_editing = True
        # Construct a properly typed LakehouseStorage to avoid type mismatch
        typed_storage: LakehouseStorage = {
            "id": storage.get("id", 0),
            "uuid": storage.get("uuid", ""),
            "name": storage.get("name", ""),
            "title": storage.get("title", ""),
            "parameters": storage.get("parameters", {}),
            "created": storage.get("created", ""),
            "modified": storage.get("modified", ""),
        }
        self.storage_to_edit = typed_storage
        self.form_data = self._get_default_form_data()
        self.form_data["name"] = typed_storage["name"]
        self.form_data["title"] = typed_storage["title"]
        for key in self.form_data["parameters"]:
            if key in typed_storage["parameters"]:
                # Don't populate secret_key field in edit mode for security
                if key == "secret_key":
                    self.form_data["parameters"][key] = ""
                else:
                    self.form_data["parameters"][key] = typed_storage["parameters"][key]
        self.form_errors = {}
        self.error_message = ""
        self.clear_secret_key = False
        self.show_storage_modal = True

    @rx.event
    def close_storage_modal(self):
        self.show_storage_modal = False
        self.storage_to_edit = None
        self.form_errors = {}
        self.clear_secret_key = False

    submit_action: str = "save"

    @rx.event
    def set_submit_action(self, action: str):
        self.submit_action = action

    @rx.event
    def toggle_clear_secret_key(self):
        """Toggle the clear secret key flag."""
        self.clear_secret_key = not self.clear_secret_key

    @rx.event
    async def handle_submit(self, form_data: dict):
        # Clear previous errors
        self.form_errors = {}
        self.error_message = ""
        # If testing connection, we handle it differently
        if self.submit_action == "test":
            async for i in self._handle_test_connection(form_data):
                yield i
            return

        submitted_name = form_data.get("name", "")
        submitted_title = form_data.get("title", "")

        # Validate required fields
        if not submitted_name.strip():
            self.form_errors = {"name": "Name is required."}
            return
        if not submitted_title.strip():
            self.form_errors = {"title": "Title is required."}
            return

        parameters = {}
        for k, v in form_data.items():
            if k.startswith("parameters."):
                key = k.split(".", 1)[1]
                parameters[key] = v

        # Handle secret key clearing in edit mode
        if self.is_editing and self.clear_secret_key:
            parameters["secret_key"] = "__CLEAR_SECRET_KEY__"

        current_form_data = self.form_data.copy()
        current_form_data["name"] = submitted_name
        current_form_data["title"] = submitted_title
        current_form_data["parameters"] = {
            **current_form_data["parameters"],
            **parameters,
        }

        try:
            api_data = {
                "name": current_form_data["name"],
                "title": current_form_data["title"],
                "parameters": current_form_data["parameters"],
            }

            headers = await self._get_headers()

            if self.is_editing and self.storage_to_edit:
                updated_storage = await lakehouse_storage_client.update(
                    self.storage_to_edit["id"], api_data, headers=headers
                )
                for i, s in enumerate(self.all_storages):
                    if s["id"] == self.storage_to_edit["id"]:
                        self.all_storages[i] = updated_storage
                        break
            else:
                new_storage = await lakehouse_storage_client.create(
                    api_data, headers=headers
                )
                self.all_storages.append(new_storage)

            yield LakehouseStorageState.close_storage_modal
        except httpx.HTTPStatusError as e:
            self.error_message = (
                f"Failed to save lakehouse storage: {str(e.response.json())}"
            )

    async def _handle_test_connection(self, form_data: dict):
        self.is_testing_connection = True
        self.error_message = ""

        try:
            # Extract parameters from form data
            parameters = {}
            for k, v in form_data.items():
                if k.startswith("parameters."):
                    key = k.split(".", 1)[1]
                    parameters[key] = v

            test_payload = {"parameters": parameters}

            # If editing, include storage_id so backend can use stored secret if needed
            if self.is_editing and self.storage_to_edit:
                test_payload["storage_id"] = self.storage_to_edit["id"]

            headers = await self._get_headers()
            result = await lakehouse_storage_client.test_connection(
                test_payload, headers=headers
            )

            if result.get("status") == "success":
                yield rx.toast.success(
                    result.get("message", "Connection successful"),
                )
            else:
                # Show error in the modal error area
                self.error_message = result.get("message", "Connection failed")
                yield rx.toast.error("Connection failed")

        except Exception as e:
            self.error_message = f"Connection test error: {str(e)}"
            yield rx.toast.error("Connection test error")

        finally:
            self.is_testing_connection = False

    @rx.event
    def open_delete_dialog(self, storage: LakehouseStorage):
        # Construct a properly typed LakehouseStorage to avoid type mismatch
        typed_storage: LakehouseStorage = {
            "id": storage.get("id", 0),
            "uuid": storage.get("uuid", ""),
            "name": storage.get("name", ""),
            "title": storage.get("title", ""),
            "parameters": storage.get("parameters", {}),
            "created": storage.get("created", ""),
            "modified": storage.get("modified", ""),
        }
        self.storage_to_delete = typed_storage
        self.show_delete_dialog = True

    @rx.event
    def close_delete_dialog(self):
        self.show_delete_dialog = False
        self.storage_to_delete = None

    @rx.event
    async def confirm_delete(self):
        if not self.storage_to_delete:
            return LakehouseStorageState.close_delete_dialog

        self.error_message = ""
        try:
            headers = await self._get_headers()
            await lakehouse_storage_client.delete(
                self.storage_to_delete["id"], headers=headers
            )
            self.all_storages = [
                s for s in self.all_storages if s["id"] != self.storage_to_delete["id"]
            ]
        except Exception as e:
            self.error_message = f"Failed to delete lakehouse storage: {str(e)}"

        return LakehouseStorageState.close_delete_dialog
