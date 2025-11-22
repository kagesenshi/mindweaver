import reflex as rx
from typing import TypedDict, Literal, Any
import datetime
import uuid
from mindweaver_fe.api_client import knowledge_db_client
from mindweaver_fe.states.project_state import ProjectState

DBType = Literal["Vector", "Graph", "Hybrid"]


class KnowledgeDB(TypedDict):
    id: int
    uuid: str
    name: str
    title: str
    description: str
    type: str
    parameters: dict[str, Any]
    created: str
    modified: str
    entry_count: int


class KnowledgeDBState(rx.State):
    """Manages the state for the knowledge database page."""

    all_databases: list[KnowledgeDB] = []
    show_db_modal: bool = False
    show_delete_dialog: bool = False
    is_editing: bool = False
    db_to_edit: KnowledgeDB | None = None
    db_to_delete: KnowledgeDB | None = None
    form_data: dict = {"name": "", "title": "", "description": "", "type": "Vector"}
    form_errors: dict = {}
    search_query: str = ""
    filter_type: str = "All"
    db_types: list[str] = ["All", "Vector", "Graph", "Hybrid"]
    is_loading: bool = False
    error_message: str = ""

    async def _get_headers(self) -> dict[str, str]:
        project_state = await self.get_state(ProjectState)
        if project_state.current_project:
            return {"X-Project-ID": str(project_state.current_project["id"])}
        return {}

    @rx.event
    async def load_databases(self):
        """Load databases from the API."""
        self.is_loading = True
        self.error_message = ""
        try:
            headers = await self._get_headers()
            databases = await knowledge_db_client.list_all(headers=headers)
            self.all_databases = databases
        except Exception as e:
            self.error_message = f"Failed to load databases: {str(e)}"
        finally:
            self.is_loading = False

    @rx.event
    def set_search_query(self, value):
        self.search_query = value

    @rx.event
    def set_filter_type(self, value):
        self.filter_type = value

    @rx.var
    def modal_db_types(self) -> list[str]:
        """Returns the list of DB types for the modal dropdown (excluding 'All')."""
        return self.db_types[1:]

    @rx.var
    def filtered_databases(self) -> list[KnowledgeDB]:
        """Returns a list of databases filtered by search query and type."""
        return [
            db
            for db in self.all_databases
            if self.search_query.lower() in db.get("name", "").lower()
            and (self.filter_type == "All" or db.get("type") == self.filter_type)
        ]

    def _validate_form(self) -> bool:
        """Validates the create/edit form data."""
        errors = {}
        if not self.form_data["name"].strip():
            errors["name"] = "Name is required."
        if not self.form_data.get("title", "").strip():
            errors["title"] = "Title is required."
        self.form_errors = errors
        return not errors

    @rx.event
    def open_create_modal(self):
        """Opens the modal to create a new database."""
        self.is_editing = False
        self.form_data = {"name": "", "title": "", "description": "", "type": "Vector"}
        self.form_errors = {}
        self.error_message = ""
        self.show_db_modal = True

    @rx.event
    def open_edit_modal(self, db: KnowledgeDB):
        """Opens the modal to edit an existing database."""
        self.is_editing = True
        # Construct a properly typed KnowledgeDB to avoid type mismatch
        typed_db: KnowledgeDB = {
            "id": db.get("id", 0),
            "uuid": db.get("uuid", ""),
            "name": db.get("name", ""),
            "title": db.get("title", ""),
            "description": db.get("description", ""),
            "type": db.get("type", "Vector"),
            "parameters": db.get("parameters", {}),
            "created": db.get("created", ""),
            "modified": db.get("modified", ""),
            "entry_count": db.get("entry_count", 0),
        }
        self.db_to_edit = typed_db
        self.form_data = {
            "name": typed_db["name"],
            "title": typed_db["title"],
            "description": typed_db["description"],
            "type": typed_db["type"],
        }
        self.form_errors = {}
        self.error_message = ""
        self.show_db_modal = True

    @rx.event
    def close_db_modal(self):
        """Closes the create/edit modal."""
        self.show_db_modal = False
        self.db_to_edit = None
        self.form_data = {"name": "", "title": "", "description": "", "type": "Vector"}
        self.form_errors = {}

    @rx.event
    def set_form_data_field(self, field: str, value: str):
        """Sets a field in the form data."""
        self.form_data[field] = value

    @rx.event
    async def handle_submit(self, form_data: dict):
        """Handles the form submission for creating or editing a database."""
        # Clear previous errors
        self.form_errors = {}
        self.error_message = ""

        self.form_data["name"] = form_data.get("name", "")
        self.form_data["title"] = form_data.get("title", "")
        self.form_data["description"] = form_data.get("description", "")

        # Validate form
        if not self._validate_form():
            return
        try:
            # Prepare data for API
            api_data = {
                "name": self.form_data["name"],
                "title": self.form_data["title"],
                "description": self.form_data.get("description", ""),
                "type": self.form_data["type"],
                "parameters": {},
            }

            headers = await self._get_headers()

            if self.is_editing and self.db_to_edit:
                # Update existing database
                updated_db = await knowledge_db_client.update(
                    self.db_to_edit["id"], api_data, headers=headers
                )
                # Update in local state
                for i, db in enumerate(self.all_databases):
                    if db["id"] == self.db_to_edit["id"]:
                        self.all_databases[i] = updated_db
                        break
            else:
                # Create new database
                new_db = await knowledge_db_client.create(api_data, headers=headers)
                self.all_databases.append(new_db)

            return KnowledgeDBState.close_db_modal
        except Exception as e:
            self.error_message = f"Failed to save database: {str(e)}"

    @rx.event
    def open_delete_dialog(self, db: KnowledgeDB):
        """Opens the confirmation dialog for deleting a database."""
        # Construct a properly typed KnowledgeDB to avoid type mismatch
        typed_db: KnowledgeDB = {
            "id": db.get("id", 0),
            "uuid": db.get("uuid", ""),
            "name": db.get("name", ""),
            "title": db.get("title", ""),
            "description": db.get("description", ""),
            "type": db.get("type", "Vector"),
            "parameters": db.get("parameters", {}),
            "created": db.get("created", ""),
            "modified": db.get("modified", ""),
            "entry_count": db.get("entry_count", 0),
        }
        self.db_to_delete = typed_db
        self.show_delete_dialog = True

    @rx.event
    def close_delete_dialog(self):
        """Closes the delete confirmation dialog."""
        self.show_delete_dialog = False
        self.db_to_delete = None

    @rx.event
    async def confirm_delete(self):
        """Deletes the selected database."""
        if not self.db_to_delete:
            return KnowledgeDBState.close_delete_dialog

        self.error_message = ""
        try:
            headers = await self._get_headers()
            await knowledge_db_client.delete(self.db_to_delete["id"], headers=headers)
            # Remove from local state
            self.all_databases = [
                db for db in self.all_databases if db["id"] != self.db_to_delete["id"]
            ]
        except Exception as e:
            self.error_message = f"Failed to delete database: {str(e)}"

        return KnowledgeDBState.close_delete_dialog
