import reflex as rx
from typing import TypedDict, Literal
import uuid
from mindweaver_fe.states.knowledge_db_state import KnowledgeDBState, KnowledgeDB

AgentStatus = Literal["Active", "Inactive"]


class AIAgent(TypedDict):
    id: str
    name: str
    model: str
    temperature: float
    system_prompt: str
    status: AgentStatus
    knowledge_db_ids: list[str]


class AIAgentsState(rx.State):
    """Manages the state for the AI agents page."""

    all_agents: list[AIAgent] = [
        {
            "id": str(uuid.uuid4()),
            "name": "Support Agent v1",
            "model": "gpt-4-turbo",
            "temperature": 0.7,
            "system_prompt": "You are a friendly and helpful customer support agent. Use the provided knowledge base to answer questions.",
            "status": "Active",
            "knowledge_db_ids": [],
        },
        {
            "id": str(uuid.uuid4()),
            "name": "Documentation Writer",
            "model": "claude-3-opus-20240229",
            "temperature": 0.5,
            "system_prompt": "You are a technical writer. You write clear, concise documentation based on the provided data.",
            "status": "Inactive",
            "knowledge_db_ids": [],
        },
    ]
    show_agent_modal: bool = False
    show_delete_dialog: bool = False
    is_editing: bool = False
    agent_to_edit: AIAgent | None = None
    agent_to_delete: AIAgent | None = None
    form_data: dict = {
        "name": "",
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
            if self.search_query.lower() in agent["name"].lower()
            and (self.filter_status == "All" or agent["status"] == self.filter_status)
        ]

    @rx.event
    async def load_knowledge_dbs(self):
        """Loads knowledge databases from the KnowledgeDBState."""
        kdb_state = await self.get_state(KnowledgeDBState)
        self.all_knowledge_dbs = kdb_state.all_databases
        if self.all_knowledge_dbs and self.all_agents:
            if not self.all_agents[0]["knowledge_db_ids"]:
                self.all_agents[0]["knowledge_db_ids"].append(
                    self.all_knowledge_dbs[0]["id"]
                )

    def _validate_form(self) -> bool:
        """Validates the agent form data."""
        errors = {}
        if not self.form_data["name"].strip():
            errors["name"] = "Name is required."
        self.form_errors = errors
        return not errors

    @rx.event
    def open_create_modal(self):
        """Opens the modal to create a new agent."""
        self.is_editing = False
        self.form_data = {
            "name": "",
            "system_prompt": "You are a helpful assistant.",
            "model": "gpt-4-turbo",
            "temperature": 0.7,
            "knowledge_db_ids": [],
        }
        self.form_errors = {}
        self.show_agent_modal = True

    @rx.event
    def open_edit_modal(self, agent: AIAgent):
        """Opens the modal to edit an existing agent."""
        self.is_editing = True
        self.agent_to_edit = agent
        self.form_data = {
            "name": agent["name"],
            "system_prompt": agent["system_prompt"],
            "model": agent["model"],
            "temperature": float(agent["temperature"]),
            "knowledge_db_ids": agent["knowledge_db_ids"].copy(),
        }
        self.form_errors = {}
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
    def handle_submit(self, form_data: dict):
        """Handles form submission for creating or editing an agent."""
        self.form_data["name"] = form_data.get("name", "")
        self.form_data["system_prompt"] = form_data.get("system_prompt", "")
        if self._validate_form():
            if self.is_editing and self.agent_to_edit:
                index_to_update = -1
                for i, agent in enumerate(self.all_agents):
                    if agent["id"] == self.agent_to_edit["id"]:
                        index_to_update = i
                        break
                if index_to_update != -1:
                    self.all_agents[index_to_update]["name"] = self.form_data["name"]
                    self.all_agents[index_to_update]["system_prompt"] = self.form_data[
                        "system_prompt"
                    ]
                    self.all_agents[index_to_update]["model"] = self.form_data["model"]
                    self.all_agents[index_to_update]["temperature"] = self.form_data[
                        "temperature"
                    ]
                    self.all_agents[index_to_update]["knowledge_db_ids"] = (
                        self.form_data["knowledge_db_ids"]
                    )
            else:
                new_agent: AIAgent = {
                    "id": str(uuid.uuid4()),
                    "name": self.form_data["name"],
                    "system_prompt": self.form_data.get("system_prompt", ""),
                    "model": self.form_data["model"],
                    "temperature": self.form_data["temperature"],
                    "status": "Inactive",
                    "knowledge_db_ids": self.form_data["knowledge_db_ids"],
                }
                self.all_agents.append(new_agent)
            return AIAgentsState.close_agent_modal

    @rx.event
    def open_delete_dialog(self, agent: AIAgent):
        """Opens the confirmation dialog for deleting an agent."""
        self.agent_to_delete = agent
        self.show_delete_dialog = True

    @rx.event
    def close_delete_dialog(self):
        """Closes the delete confirmation dialog."""
        self.show_delete_dialog = False
        self.agent_to_delete = None

    @rx.event
    def confirm_delete(self):
        """Deletes the selected agent."""
        if self.agent_to_delete:
            self.all_agents = [
                agent
                for agent in self.all_agents
                if agent["id"] != self.agent_to_delete["id"]
            ]
        return AIAgentsState.close_delete_dialog