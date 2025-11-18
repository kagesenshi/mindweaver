import reflex as rx
from typing import TypedDict, Literal
import uuid
import datetime
import asyncio
from mindweaver_fe.states.ai_agents_state import AIAgentsState, AIAgent
from mindweaver_fe.states.knowledge_db_state import KnowledgeDB, KnowledgeDBState


class Message(TypedDict):
    role: Literal["user", "assistant"]
    content: str
    timestamp: str


class ConversationInfo(TypedDict):
    id: str
    title: str


class ChatState(rx.State):
    """Manages the state for the chat page."""

    all_agents: list[AIAgent] = []
    all_dbs: list[KnowledgeDB] = []
    selected_agent_id: str = ""
    conversations: dict[str, list[Message]] = {}
    conversation_history: list[ConversationInfo] = []
    current_conversation_id: str | None = None
    input_message: str = ""
    is_streaming: bool = False

    @rx.event
    def set_input_message(self, value):
        self.input_message = value

    @rx.event
    async def load_initial_data(self):
        """Load agents and knowledge bases on page mount."""
        agent_state = await self.get_state(AIAgentsState)
        self.all_agents = agent_state.all_agents
        kdb_state = await self.get_state(KnowledgeDBState)
        self.all_dbs = kdb_state.all_databases

    @rx.var
    def selected_agent(self) -> AIAgent | None:
        """The currently selected AI agent."""
        if self.selected_agent_id and self.all_agents:
            for agent in self.all_agents:
                if agent["id"] == self.selected_agent_id:
                    return agent
        return None

    @rx.var
    def connected_dbs(self) -> list[KnowledgeDB]:
        """List of knowledge DBs connected to the selected agent."""
        if self.selected_agent and self.all_dbs:
            connected_ids = self.selected_agent["knowledge_db_ids"]
            return [db for db in self.all_dbs if db["id"] in connected_ids]
        return []

    @rx.var
    def current_conversation_messages(self) -> list[Message]:
        """The messages for the currently selected conversation."""
        if (
            self.current_conversation_id
            and self.current_conversation_id in self.conversations
        ):
            return self.conversations[self.current_conversation_id]
        return []

    @rx.event
    def select_conversation(self, conv_id: str):
        """Select an existing conversation from the history."""
        self.current_conversation_id = conv_id

    @rx.event
    def create_new_conversation(self):
        """Start a new conversation."""
        new_id = str(uuid.uuid4())
        self.current_conversation_id = new_id
        self.conversations[new_id] = []
        new_conv_info: ConversationInfo = {
            "id": new_id,
            "title": f"Conversation {len(self.conversation_history) + 1}",
        }
        self.conversation_history.insert(0, new_conv_info)

    @rx.event
    def set_agent_and_start_chat(self, agent_id: str):
        """Select an agent and start a new chat if none exists."""
        self.selected_agent_id = agent_id
        if not self.current_conversation_id:
            return ChatState.create_new_conversation

    @rx.event
    async def handle_send_message(self, form_data: dict):
        """Handle sending a message from the user."""
        message_content = form_data.get("input_message", "").strip()
        if (
            not message_content
            or not self.current_conversation_id
            or (not self.selected_agent)
        ):
            return
        self.input_message = ""
        user_message: Message = {
            "role": "user",
            "content": message_content,
            "timestamp": datetime.datetime.now().strftime("%H:%M"),
        }
        self.conversations[self.current_conversation_id].append(user_message)
        if len(self.conversations[self.current_conversation_id]) == 1:
            for i, conv in enumerate(self.conversation_history):
                if conv["id"] == self.current_conversation_id:
                    title = message_content[:25] + (
                        "..." if len(message_content) > 25 else ""
                    )
                    self.conversation_history[i]["title"] = title
                    break
        self.is_streaming = True
        yield
        assistant_response = f"This is a streamed response about '{message_content[:20]}...'. I am {self.selected_agent['name']}."
        assistant_message: Message = {
            "role": "assistant",
            "content": "",
            "timestamp": datetime.datetime.now().strftime("%H:%M"),
        }
        self.conversations[self.current_conversation_id].append(assistant_message)
        for chunk in assistant_response.split():
            self.conversations[self.current_conversation_id][-1]["content"] += (
                chunk + " "
            )
            await asyncio.sleep(0.05)
            yield
        self.is_streaming = False