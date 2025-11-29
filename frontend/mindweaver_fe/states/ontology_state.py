import reflex as rx
from typing import TypedDict, List, Any, Optional
from mindweaver_fe.api_client import ontology_client
from mindweaver_fe.states.project_state import ProjectState
import httpx


class EntityAttribute(TypedDict):
    id: int
    name: str
    data_type: str
    required: bool


class RelationshipAttribute(TypedDict):
    id: int
    name: str
    data_type: str
    required: bool


class EntityType(TypedDict):
    id: int
    name: str
    description: str
    attributes: List[EntityAttribute]


class RelationshipType(TypedDict):
    id: int
    name: str
    description: str
    source_entity_type: str
    target_entity_type: str
    attributes: List[RelationshipAttribute]


class Ontology(TypedDict):
    id: int
    name: str
    title: str
    description: str
    entity_types: List[EntityType]
    relationship_types: List[RelationshipType]
    created: str
    modified: str


class OntologyState(rx.State):
    """Manages the state for the ontology page."""

    ontologies: List[Ontology] = []
    is_loading: bool = False
    error_message: str = ""

    show_modal: bool = False
    is_editing: bool = False
    current_ontology: Optional[Ontology] = None

    form_data: dict = {"name": "", "title": "", "description": ""}
    form_errors: dict = {}

    async def _get_headers(self) -> dict[str, str]:
        project_state = await self.get_state(ProjectState)
        if project_state.current_project:
            return {"X-Project-ID": str(project_state.current_project["id"])}
        return {}

    @rx.event
    async def load_ontologies(self):
        """Load ontologies from the API."""
        self.is_loading = True
        self.error_message = ""
        try:
            headers = await self._get_headers()
            self.ontologies = await ontology_client.list_all(headers=headers)
        except Exception as e:
            self.error_message = f"Failed to load ontologies: {str(e)}"
        finally:
            self.is_loading = False

    @rx.event
    def open_create_modal(self):
        self.is_editing = False
        self.form_data = {"name": "", "title": "", "description": ""}
        self.form_errors = {}
        self.show_modal = True

    @rx.event
    def open_edit_modal(self, ontology: Ontology):
        self.is_editing = True
        self.current_ontology = ontology
        self.form_data = {
            "name": ontology["name"],
            "title": ontology["title"],
            "description": ontology["description"],
        }
        self.form_errors = {}
        self.show_modal = True

    @rx.event
    def close_modal(self):
        self.show_modal = False
        self.current_ontology = None
        self.form_data = {"name": "", "title": "", "description": ""}
        self.form_errors = {}

    @rx.event
    def set_form_data(self, field: str, value: str):
        self.form_data[field] = value

    @rx.event
    async def handle_submit(self):
        # Clear previous errors
        self.form_errors = {}
        self.error_message = ""

        if not self.form_data["name"]:
            self.form_errors = {"name": "Name is required"}
            return

        if not self.form_data["title"]:
            self.form_errors = {"title": "Title is required"}
            return

        try:
            headers = await self._get_headers()
            if self.is_editing and self.current_ontology:
                # Update
                updated = await ontology_client.update(
                    self.current_ontology["id"], self.form_data, headers=headers
                )
                # Refresh list or update local
                await self.load_ontologies()
            else:
                # Create
                await ontology_client.create(self.form_data, headers=headers)
                await self.load_ontologies()

            self.close_modal()
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
                            f"Failed to save ontology: {str(error_data)}"
                        )
                else:
                    self.error_message = f"Failed to save ontology: {str(error_data)}"
            except Exception:
                self.error_message = f"Failed to save ontology: {str(e)}"
        except Exception as e:
            self.error_message = f"Failed to save ontology: {str(e)}"
