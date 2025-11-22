import reflex as rx
from typing import TypedDict, Literal, Union, Optional, Any
import uuid
import datetime
import asyncio
import logging
from mindweaver_fe.states.knowledge_db_state import KnowledgeDB, KnowledgeDBState
from mindweaver_fe.states.project_state import ProjectState
from mindweaver_fe.api_client import data_source_client
import httpx

SourceType = Literal["API", "Database", "File Upload", "Web Scraper"]
SourceStatus = Literal["Connected", "Disconnected", "Error"]
ImportStatus = Literal["Running", "Completed", "Failed"]


class APIConfig(TypedDict):
    base_url: str
    api_key: str


class DBConfig(TypedDict):
    host: str
    port: int
    username: str
    password: str
    database_type: str


class WebScraperConfig(TypedDict):
    start_url: str


class FileUploadConfig(TypedDict):
    pass


class DataSourceFormData(TypedDict):
    name: str
    title: str
    source_type: SourceType
    parameters: Union[APIConfig, DBConfig, WebScraperConfig, FileUploadConfig]


class DataSource(TypedDict):
    id: int
    uuid: str
    name: str
    title: str
    type: str
    parameters: dict[str, Any]
    created: str
    modified: str
    status: str
    last_sync: str


class DataSourcesState(rx.State):
    """Manages the state for the data sources page."""

    all_sources: list[DataSource] = []
    all_knowledge_dbs: list[KnowledgeDB] = []
    show_source_modal: bool = False
    show_delete_dialog: bool = False
    is_editing: bool = False
    source_to_edit: DataSource | None = None
    source_to_delete: DataSource | None = None
    form_data: DataSourceFormData = {
        "name": "",
        "title": "",
        "source_type": "API",
        "parameters": {"base_url": "http://www.google.com", "api_key": "..."},
    }
    form_errors: dict = {}
    search_query: str = ""
    filter_type: str = "All"
    source_type_options: list[str] = ["API", "Database", "File Upload", "Web Scraper"]
    filter_type_options: list[str] = ["All"] + source_type_options
    is_testing_connection: bool = False
    is_loading: bool = False
    error_message: str = ""
    clear_password: bool = False  # Flag to clear password in edit mode

    def _get_default_form_data(
        self, source_type: SourceType = "API"
    ) -> DataSourceFormData:
        parameters: Union[APIConfig, DBConfig, WebScraperConfig, FileUploadConfig]
        if source_type == "API":
            parameters = {"base_url": "http://www.google.com", "api_key": "asfsadfsadf"}
        elif source_type == "Database":
            parameters = {
                "host": "192.168.0.1",
                "port": 5432,
                "username": "asd",
                "password": "",
                "database_type": "postgresql",
            }
        elif source_type == "Web Scraper":
            parameters = {"start_url": "http://www.google.com"}
        else:
            parameters = {}
        return {
            "name": "",
            "title": "",
            "source_type": source_type,
            "parameters": parameters,
        }

    @rx.event
    async def set_search_query(self, value):
        self.search_query = value

    @rx.event
    async def set_filter_type(self, value):
        self.filter_type = value

    async def _get_headers(self) -> dict[str, str]:
        project_state = await self.get_state(ProjectState)
        if project_state.current_project:
            return {"X-Project-ID": str(project_state.current_project["id"])}
        return {}

    @rx.event
    async def load_initial_data(self):
        """Load knowledge bases and data sources from API."""
        self.is_loading = True
        self.error_message = ""
        try:
            kdb_state = await self.get_state(KnowledgeDBState)
            await kdb_state.load_databases()
            self.all_knowledge_dbs = kdb_state.all_databases

            # Load sources from API
            headers = await self._get_headers()
            sources = await data_source_client.list_all(headers=headers)
            self.all_sources = sources
        except Exception as e:
            self.error_message = f"Failed to load data: {str(e)}"
        finally:
            self.is_loading = False

    @rx.var
    def filtered_sources(self) -> list[DataSource]:
        return [
            source
            for source in self.all_sources
            if self.search_query.lower() in source.get("name", "").lower()
            and (self.filter_type == "All" or source.get("type") == self.filter_type)
        ]

    @rx.event
    def open_create_modal(self):
        self.is_editing = False
        self.form_data = self._get_default_form_data()
        self.form_errors = {}
        self.error_message = ""
        self.show_source_modal = True

    @rx.event
    def open_edit_modal(self, source: DataSource):
        self.is_editing = True
        # Construct a properly typed DataSource to avoid type mismatch
        typed_source: DataSource = {
            "id": source.get("id", 0),
            "uuid": source.get("uuid", ""),
            "name": source.get("name", ""),
            "title": source.get("title", ""),
            "type": source.get("type", "API"),
            "parameters": source.get("parameters", {}),
            "created": source.get("created", ""),
            "modified": source.get("modified", ""),
            "status": source.get("status", "Disconnected"),
            "last_sync": source.get("last_sync", "Never"),
        }
        self.source_to_edit = typed_source
        source_type = typed_source["type"]
        self.form_data = self._get_default_form_data(source_type)
        self.form_data["name"] = typed_source["name"]
        self.form_data["title"] = typed_source["title"]
        self.form_data["source_type"] = source_type
        for key in self.form_data["parameters"]:
            if key in typed_source["parameters"]:
                # Don't populate password field in edit mode for security
                if key == "password":
                    self.form_data["parameters"][key] = ""
                else:
                    self.form_data["parameters"][key] = typed_source["parameters"][key]
        self.form_errors = {}
        self.error_message = ""
        self.clear_password = False
        self.show_source_modal = True

    @rx.event
    def close_source_modal(self):
        self.show_source_modal = False
        self.source_to_edit = None
        self.form_errors = {}
        self.clear_password = False

    submit_action: str = "save"

    @rx.event
    def set_submit_action(self, action: str):
        self.submit_action = action

    @rx.event
    def toggle_clear_password(self):
        """Toggle the clear password flag."""
        self.clear_password = not self.clear_password

    @rx.event
    def set_form_data_field(self, field: str, value: str):
        if field == "source_type":
            self.form_data = self._get_default_form_data(value)
            self.form_data["name"] = self.form_data.get("name", "")
            self.form_data["title"] = self.form_data.get("title", "")
        else:
            self.form_data[field] = value

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
                if key == "port":
                    try:
                        parameters[key] = int(v)
                    except (ValueError, TypeError) as e:
                        logging.exception(f"Error converting port to int: {e}")
                        parameters[key] = 0
                else:
                    parameters[key] = v

        # Handle password clearing in edit mode
        if self.is_editing and self.clear_password:
            parameters["password"] = "__CLEAR_PASSWORD__"

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
                "type": current_form_data["source_type"],
                "parameters": current_form_data["parameters"],
            }

            headers = await self._get_headers()

            if self.is_editing and self.source_to_edit:
                updated_source = await data_source_client.update(
                    self.source_to_edit["id"], api_data, headers=headers
                )
                for i, s in enumerate(self.all_sources):
                    if s["id"] == self.source_to_edit["id"]:
                        self.all_sources[i] = updated_source
                        break
            else:
                new_source = await data_source_client.create(api_data, headers=headers)
                self.all_sources.append(new_source)

            yield DataSourcesState.close_source_modal
        except httpx.HTTPStatusError as e:
            self.error_message = f"Failed to save data source: {str(e.response.json())}"

    async def _handle_test_connection(self, form_data: dict):
        self.is_testing_connection = True
        self.error_message = ""

        try:
            # Extract parameters from form data
            parameters = {}
            for k, v in form_data.items():
                if k.startswith("parameters."):
                    key = k.split(".", 1)[1]
                    if key == "port":
                        try:
                            parameters[key] = int(v)
                        except (ValueError, TypeError):
                            parameters[key] = 0
                    else:
                        parameters[key] = v

            # Use current source type from state (it's controlled)
            source_type = self.form_data.get("source_type")

            test_payload = {"type": source_type, "parameters": parameters}

            # If editing, include source_id so backend can use stored password if needed
            if self.is_editing and self.source_to_edit:
                test_payload["source_id"] = self.source_to_edit["id"]

            headers = await self._get_headers()
            result = await data_source_client.test_connection(
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
    def open_delete_dialog(self, source: DataSource):
        # Construct a properly typed DataSource to avoid type mismatch
        typed_source: DataSource = {
            "id": source.get("id", 0),
            "uuid": source.get("uuid", ""),
            "name": source.get("name", ""),
            "title": source.get("title", ""),
            "type": source.get("type", "API"),
            "parameters": source.get("parameters", {}),
            "created": source.get("created", ""),
            "modified": source.get("modified", ""),
            "status": source.get("status", "Disconnected"),
            "last_sync": source.get("last_sync", "Never"),
        }
        self.source_to_delete = typed_source
        self.show_delete_dialog = True

    @rx.event
    def close_delete_dialog(self):
        self.show_delete_dialog = False
        self.source_to_delete = None

    @rx.event
    async def confirm_delete(self):
        if not self.source_to_delete:
            return DataSourcesState.close_delete_dialog

        self.error_message = ""
        try:
            headers = await self._get_headers()
            await data_source_client.delete(
                self.source_to_delete["id"], headers=headers
            )
            self.all_sources = [
                s for s in self.all_sources if s["id"] != self.source_to_delete["id"]
            ]
        except Exception as e:
            self.error_message = f"Failed to delete data source: {str(e)}"

        return DataSourcesState.close_delete_dialog

    @rx.event
    def open_ingest_dialog(self, source: DataSource):
        """Navigate to ingestion page with pre-selected data source."""
        # Set the preselected data source ID in ingestion state
        from mindweaver_fe.states.ingestion_state import IngestionState

        # This will be picked up when the ingestion page loads
        return rx.redirect("/ingestion")
