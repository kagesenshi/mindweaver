import reflex as rx
from typing import TypedDict, Literal, Any
import uuid
import datetime
import asyncio
from mindweaver_fe.states.ai_agents_state import AIAgentsState, AIAgent
from mindweaver_fe.states.knowledge_db_state import KnowledgeDB, KnowledgeDBState
from mindweaver_fe.api_client import chat_client


class Message(TypedDict):
    role: Literal["user", "assistant"]
    content: str
    timestamp: str


class Chat(TypedDict):
    id: int
    uuid: str
    name: str
    title: str
    messages: list[dict[str, Any]]
    agent_id: str | None
    created: str
    modified: str


class ConversationInfo(TypedDict):
    id: int
    title: str


class ChatState(rx.State):
    """Manages the state for the chat page."""

    all_agents: list[AIAgent] = []
    all_dbs: list[KnowledgeDB] = []
    all_chats: list[Chat] = []
    selected_agent_id: str = ""
    current_conversation_id: int | None = None
    input_message: str = ""
    is_streaming: bool = False
    is_loading: bool = False
    error_message: str = ""

    @rx.event
    def set_input_message(self, value):
        self.input_message = value

    @rx.event
    async def load_initial_data(self):
        """Load agents, knowledge bases, and chats on page mount."""
        self.is_loading = True
        self.error_message = ""
        try:
            agent_state = await self.get_state(AIAgentsState)
            await agent_state.load_agents()
            self.all_agents = agent_state.all_agents
            
            kdb_state = await self.get_state(KnowledgeDBState)
            await kdb_state.load_databases()
            self.all_dbs = kdb_state.all_databases
            
            # Load chats from API
            chats = await chat_client.list_all()
            self.all_chats = chats
        except Exception as e:
            self.error_message = f"Failed to load data: {str(e)}"
        finally:
            self.is_loading = False

    @rx.var
    def selected_agent(self) -> AIAgent | None:
        """The currently selected AI agent."""
        if self.selected_agent_id and self.all_agents:
            for agent in self.all_agents:
                if str(agent["id"]) == self.selected_agent_id:
                    return agent
        return None

    @rx.var
    def connected_dbs(self) -> list[KnowledgeDB]:
        """List of knowledge DBs connected to the selected agent."""
        if self.selected_agent and self.all_dbs:
            connected_ids = self.selected_agent.get("knowledge_db_ids", [])
            return [db for db in self.all_dbs if str(db["id"]) in connected_ids]
        return []

    @rx.var
    def current_conversation_messages(self) -> list[Message]:
        """The messages for the currently selected conversation."""
        if self.current_conversation_id:
            for chat in self.all_chats:
                if chat["id"] == self.current_conversation_id:
                    return chat.get("messages", [])
        return []

    @rx.var
    def conversation_history(self) -> list[ConversationInfo]:
        """List of conversation info for the sidebar."""
        return [
            {
                "id": chat["id"],
                "title": chat.get("title", chat.get("name", f"Chat {chat['id']}"))
            }
            for chat in self.all_chats
        ]

    @rx.event
    def select_conversation(self, conv_id: int):
        """Select an existing conversation from the history."""
        self.current_conversation_id = conv_id

    @rx.event
    async def create_new_conversation(self):
        """Start a new conversation."""
        self.error_message = ""
        try:
            # Create new chat in backend
            new_chat_data = {
                "name": f"chat-{datetime.datetime.now().strftime('%Y%m%d-%H%M%S')}",
                "title": f"Conversation {len(self.all_chats) + 1}",
                "messages": [],
                "agent_id": self.selected_agent_id if self.selected_agent_id else None
            }
            new_chat = await chat_client.create(new_chat_data)
            self.all_chats.insert(0, new_chat)
            self.current_conversation_id = new_chat["id"]
        except Exception as e:
            self.error_message = f"Failed to create conversation: {str(e)}"

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
        self.error_message = ""
        
        # Find current chat
        current_chat = None
        chat_index = -1
        for i, chat in enumerate(self.all_chats):
            if chat["id"] == self.current_conversation_id:
                current_chat = chat
                chat_index = i
                break
        
        if not current_chat:
            return
        
        # Add user message
        user_message: Message = {
            "role": "user",
            "content": message_content,
            "timestamp": datetime.datetime.now().strftime("%H:%M"),
        }
        
        messages = current_chat.get("messages", []).copy()
        messages.append(user_message)
        
        # Update title if first message
        title = current_chat.get("title", "")
        if len(messages) == 1:
            title = message_content[:25] + ("..." if len(message_content) > 25 else "")
        
        # Simulate streaming response
        self.is_streaming = True
        yield
        
        assistant_response = f"This is a streamed response about '{message_content[:20]}...'. I am {self.selected_agent['name']}."
        assistant_message: Message = {
            "role": "assistant",
            "content": "",
            "timestamp": datetime.datetime.now().strftime("%H:%M"),
        }
        messages.append(assistant_message)
        
        # Update local state with streaming
        for chunk in assistant_response.split():
            messages[-1]["content"] += chunk + " "
            self.all_chats[chat_index]["messages"] = messages
            await asyncio.sleep(0.05)
            yield
        
        self.is_streaming = False
        
        # Save to backend
        try:
            update_data = {
                "title": title,
                "messages": messages,
                "agent_id": self.selected_agent_id
            }
            updated_chat = await chat_client.update(self.current_conversation_id, update_data)
            self.all_chats[chat_index] = updated_chat
        except Exception as e:
            self.error_message = f"Failed to save message: {str(e)}"