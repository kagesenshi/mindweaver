import reflex as rx
from typing import TypedDict, Literal, Any
import uuid
from mindweaver_fe.states.knowledge_db_state import KnowledgeDBState, KnowledgeDB
from mindweaver_fe.api_client import ai_agent_client
from mindweaver_fe.states.project_state import ProjectState
import httpx

AgentStatus = Literal["Active", "Inactive"]


class AIAgent(TypedDict):
    id: int
    uuid: str
    name: str
    title: str
    model: str
    temperature: float
    system_prompt: str
    status: AgentStatus
    knowledge_db_ids: list[str]
    created: str
    modified: str


class AIAgentsState(rx.State):
    """Manages the state for the AI agents page."""

    all_agents: list[AIAgent] = []
    show_agent_modal: bool = False
    show_delete_dialog: bool = False
    is_editing: bool = False
    agent_to_edit: AIAgent | None = None
    agent_to_delete: AIAgent | None = None
    form_data: dict = {
        "name": "",
        "title": "",
        "system_prompt": "",
        "model": "gpt-4-turbo",
        "temperature": 0.7,
        "knowledge_db_ids": [],
    }
    form_errors: dict = {}
    search_query: str = ""
    filter_status: str = "All"
    status_options: list[str] = ["All", "Active", "Inactive"]
    available_models: list[str] = [
        "gpt-4-turbo",
        "gpt-3.5-turbo",
        "claude-3-opus-20240229",
        "claude-3-sonnet-20240229",
    ]
    all_knowledge_dbs: list[KnowledgeDB] = []
    is_loading: bool = False
    error_message: str = ""

    async def _get_headers(self) -> dict[str, str]:
        project_state = await self.get_state(ProjectState)
        if project_state.current_project:
            return {"X-Project-ID": str(project_state.current_project["id"])}
        return {}

    @rx.event
    async def load_agents(self):
        """Load agents and knowledge databases from the API."""
        self.is_loading = True
        self.error_message = ""
        try:
            # Load knowledge databases first
            kdb_state = await self.get_state(KnowledgeDBState)
            await kdb_state.load_databases()
            self.all_knowledge_dbs = kdb_state.all_databases

            # Load agents
            headers = await self._get_headers()
            agents = await ai_agent_client.list_all(headers=headers)
            self.all_agents = agents
        except Exception as e:
            self.error_message = f"Failed to load data: {str(e)}"
        finally:
            self.is_loading = False

    @rx.event
    async def set_search_query(self, value):
        self.search_query = value

    @rx.event
    async def set_filter_status(self, value):
        self.filter_status = value

    @rx.var
    def filtered_agents(self) -> list[AIAgent]:
        """Returns a list of agents filtered by search query and status."""
        return [
            agent
            for agent in self.all_agents
            if self.search_query.lower() in agent.get("name", "").lower()
            and (
                self.filter_status == "All" or agent.get("status") == self.filter_status
            )
        ]

    @rx.event
    async def load_knowledge_dbs(self):
        """Loads knowledge databases from the KnowledgeDBState."""
        kdb_state = await self.get_state(KnowledgeDBState)
        await kdb_state.load_databases()
        self.all_knowledge_dbs = kdb_state.all_databases

    def _validate_form(self) -> bool:
        """Validates the agent form data."""
        errors = {}
        if not self.form_data["name"].strip():
            errors["name"] = "Name is required."
        if not self.form_data.get("title", "").strip():
            errors["title"] = "Title is required."
        self.form_errors = errors
        return not errors

    @rx.event
    def open_create_modal(self):
        """Opens the modal to create a new agent."""
        self.is_editing = False
        self.form_data = {
            "name": "",
            "title": "",
            "system_prompt": "You are a helpful assistant.",
            "model": "gpt-4-turbo",
            "temperature": 0.7,
            "knowledge_db_ids": [],
        }
        self.form_errors = {}
        self.error_message = ""
        self.show_agent_modal = True

    @rx.event
    def open_edit_modal(self, agent: AIAgent):
        """Opens the modal to edit an existing agent."""
        self.is_editing = True
        # Construct a properly typed AIAgent to avoid type mismatch
        typed_agent: AIAgent = {
            "id": agent.get("id", 0),
            "uuid": agent.get("uuid", ""),
            "name": agent.get("name", ""),
            "title": agent.get("title", ""),
            "model": agent.get("model", "gpt-4-turbo"),
            "temperature": agent.get("temperature", 0.7),
            "system_prompt": agent.get("system_prompt", ""),
            "status": agent.get("status", "Inactive"),
            "knowledge_db_ids": agent.get("knowledge_db_ids", []),
            "created": agent.get("created", ""),
            "modified": agent.get("modified", ""),
        }
        self.agent_to_edit = typed_agent
        self.form_data = {
            "name": typed_agent["name"],
            "title": typed_agent["title"],
            "system_prompt": typed_agent["system_prompt"],
            "model": typed_agent["model"],
            "temperature": float(typed_agent["temperature"]),
            "knowledge_db_ids": (
                typed_agent["knowledge_db_ids"].copy()
                if typed_agent["knowledge_db_ids"]
                else []
            ),
        }
        self.form_errors = {}
        self.error_message = ""
        self.show_agent_modal = True

    @rx.event
    def close_agent_modal(self):
        """Closes the create/edit agent modal."""
        self.show_agent_modal = False
        self.agent_to_edit = None
        self.form_errors = {}

    @rx.event
    def set_form_data_field(self, field: str, value: str | float):
        """Sets a field in the form data."""
        if field == "temperature":
            self.form_data[field] = float(value)
        else:
            self.form_data[field] = value

    @rx.event
    def toggle_db_selection(self, db_id: str, checked: bool):
        """Toggles the selection of a knowledge DB in the form."""
        if checked:
            if db_id not in self.form_data["knowledge_db_ids"]:
                self.form_data["knowledge_db_ids"].append(db_id)
        elif db_id in self.form_data["knowledge_db_ids"]:
            self.form_data["knowledge_db_ids"].remove(db_id)

    @rx.event
    async def handle_submit(self, form_data: dict):
        """Handles form submission for creating or editing an agent."""
        # Clear previous errors
        self.form_errors = {}
        self.error_message = ""

        self.form_data["name"] = form_data.get("name", "")
        self.form_data["title"] = form_data.get("title", "")
        self.form_data["system_prompt"] = form_data.get("system_prompt", "")

        # Validate form
        if not self._validate_form():
            return
        try:
            # Prepare data for API
            api_data = {
                "name": self.form_data["name"],
                "title": self.form_data["title"],
                "system_prompt": self.form_data.get("system_prompt", ""),
                "model": self.form_data["model"],
                "temperature": self.form_data["temperature"],
                "status": "Inactive",
                "knowledge_db_ids": self.form_data["knowledge_db_ids"],
            }

            headers = await self._get_headers()

            if self.is_editing and self.agent_to_edit:
                # Update existing agent
                api_data["status"] = self.agent_to_edit.get("status", "Inactive")
                updated_agent = await ai_agent_client.update(
                    self.agent_to_edit["id"], api_data, headers=headers
                )
                # Update in local state
                for i, agent in enumerate(self.all_agents):
                    if agent["id"] == self.agent_to_edit["id"]:
                        self.all_agents[i] = updated_agent
                        break
            else:
                # Create new agent
                new_agent = await ai_agent_client.create(api_data, headers=headers)
                self.all_agents.append(new_agent)

            return AIAgentsState.close_agent_modal
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
                        self.error_message = f"Failed to save agent: {str(error_data)}"
                else:
                    self.error_message = f"Failed to save agent: {str(error_data)}"
            except Exception:
                self.error_message = f"Failed to save agent: {str(e)}"
        except Exception as e:
            self.error_message = f"Failed to save agent: {str(e)}"

    @rx.event
    def open_delete_dialog(self, agent: AIAgent):
        """Opens the confirmation dialog for deleting an agent."""
        # Construct a properly typed AIAgent to avoid type mismatch
        typed_agent: AIAgent = {
            "id": agent.get("id", 0),
            "uuid": agent.get("uuid", ""),
            "name": agent.get("name", ""),
            "title": agent.get("title", ""),
            "model": agent.get("model", "gpt-4-turbo"),
            "temperature": agent.get("temperature", 0.7),
            "system_prompt": agent.get("system_prompt", ""),
            "status": agent.get("status", "Inactive"),
            "knowledge_db_ids": agent.get("knowledge_db_ids", []),
            "created": agent.get("created", ""),
            "modified": agent.get("modified", ""),
        }
        self.agent_to_delete = typed_agent
        self.show_delete_dialog = True

    @rx.event
    def close_delete_dialog(self):
        """Closes the delete confirmation dialog."""
        self.show_delete_dialog = False
        self.agent_to_delete = None

    @rx.event
    async def confirm_delete(self):
        """Deletes the selected agent."""
        if not self.agent_to_delete:
            return AIAgentsState.close_delete_dialog

        self.error_message = ""
        try:
            headers = await self._get_headers()
            await ai_agent_client.delete(self.agent_to_delete["id"], headers=headers)
            # Remove from local state
            self.all_agents = [
                agent
                for agent in self.all_agents
                if agent["id"] != self.agent_to_delete["id"]
            ]
        except httpx.HTTPStatusError as e:
            try:
                error_data = e.response.json()
                self.error_message = (
                    f"Failed to delete agent: {error_data.get('detail', str(e))}"
                )
            except Exception:
                self.error_message = f"Failed to delete agent: {str(e)}"
        except Exception as e:
            self.error_message = f"Failed to delete agent: {str(e)}"

        return AIAgentsState.close_delete_dialog
