import reflex as rx
from typing import TypedDict, Literal
import datetime
import uuid

DBType = Literal["Vector", "Graph", "Hybrid"]


class KnowledgeDB(TypedDict):
    id: str
    name: str
    description: str
    db_type: DBType
    entry_count: int
    created_at: str


class KnowledgeDBState(rx.State):
    """Manages the state for the knowledge database page."""

    all_databases: list[KnowledgeDB] = [
        {
            "id": str(uuid.uuid4()),
            "name": "Project Phoenix Docs",
            "description": "Internal documentation for Project Phoenix, focusing on architecture and design patterns.",
            "db_type": "Vector",
            "entry_count": 1250,
            "created_at": "2023-10-26",
        },
        {
            "id": str(uuid.uuid4()),
            "name": "Customer Support Tickets",
            "description": "A graph-based knowledge base of interconnected customer issues and resolutions.",
            "db_type": "Graph",
            "entry_count": 5400,
            "created_at": "2023-09-15",
        },
        {
            "id": str(uuid.uuid4()),
            "name": "Q3 Financial Reports",
            "description": "Hybrid database containing both vector embeddings of reports and a graph of financial entities.",
            "db_type": "Hybrid",
            "entry_count": 350,
            "created_at": "2023-10-02",
        },
    ]
    show_db_modal: bool = False
    show_delete_dialog: bool = False
    is_editing: bool = False
    db_to_edit: KnowledgeDB | None = None
    db_to_delete: KnowledgeDB | None = None
    form_data: dict = {"name": "", "description": "", "db_type": "Vector"}
    form_errors: dict = {}
    search_query: str = ""
    filter_type: str = "All"
    db_types: list[str] = ["All", "Vector", "Graph", "Hybrid"]

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
            if self.search_query.lower() in db["name"].lower()
            and (self.filter_type == "All" or db["db_type"] == self.filter_type)
        ]

    def _validate_form(self) -> bool:
        """Validates the create/edit form data."""
        errors = {}
        if not self.form_data["name"].strip():
            errors["name"] = "Name is required."
        self.form_errors = errors
        return not errors

    @rx.event
    def open_create_modal(self):
        """Opens the modal to create a new database."""
        self.is_editing = False
        self.form_data = {"name": "", "description": "", "db_type": "Vector"}
        self.form_errors = {}
        self.show_db_modal = True

    @rx.event
    def open_edit_modal(self, db: KnowledgeDB):
        """Opens the modal to edit an existing database."""
        self.is_editing = True
        self.db_to_edit = db
        self.form_data = {
            "name": db["name"],
            "description": db["description"],
            "db_type": db["db_type"],
        }
        self.form_errors = {}
        self.show_db_modal = True

    @rx.event
    def close_db_modal(self):
        """Closes the create/edit modal."""
        self.show_db_modal = False
        self.db_to_edit = None
        self.form_data = {"name": "", "description": "", "db_type": "Vector"}
        self.form_errors = {}

    @rx.event
    def set_form_data_field(self, field: str, value: str):
        """Sets a field in the form data."""
        self.form_data[field] = value

    @rx.event
    def handle_submit(self, form_data: dict):
        """Handles the form submission for creating or editing a database."""
        self.form_data["name"] = form_data.get("name", "")
        self.form_data["description"] = form_data.get("description", "")
        if self._validate_form():
            if self.is_editing and self.db_to_edit:
                index_to_update = -1
                for i, db in enumerate(self.all_databases):
                    if db["id"] == self.db_to_edit["id"]:
                        index_to_update = i
                        break
                if index_to_update != -1:
                    self.all_databases[index_to_update]["name"] = self.form_data["name"]
                    self.all_databases[index_to_update]["description"] = self.form_data[
                        "description"
                    ]
                    self.all_databases[index_to_update]["db_type"] = self.form_data[
                        "db_type"
                    ]
            else:
                new_db: KnowledgeDB = {
                    "id": str(uuid.uuid4()),
                    "name": self.form_data["name"],
                    "description": self.form_data.get("description", ""),
                    "db_type": self.form_data["db_type"],
                    "entry_count": 0,
                    "created_at": datetime.date.today().isoformat(),
                }
                self.all_databases.append(new_db)
            return KnowledgeDBState.close_db_modal

    @rx.event
    def open_delete_dialog(self, db: KnowledgeDB):
        """Opens the confirmation dialog for deleting a database."""
        self.db_to_delete = db
        self.show_delete_dialog = True

    @rx.event
    def close_delete_dialog(self):
        """Closes the delete confirmation dialog."""
        self.show_delete_dialog = False
        self.db_to_delete = None

    @rx.event
    def confirm_delete(self):
        """Deletes the selected database."""
        if self.db_to_delete:
            self.all_databases = [
                db for db in self.all_databases if db["id"] != self.db_to_delete["id"]
            ]
        return KnowledgeDBState.close_delete_dialog