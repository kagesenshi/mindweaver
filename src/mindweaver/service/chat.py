from . import NamedBase, Base
from . import Service
from sqlalchemy import String
from sqlalchemy_utils import JSONType
from sqlmodel import Field, Relationship
from typing import Any

class Chat(NamedBase, table=True):
    __tablename__ = 'mw_chat'
    messages: list[dict[str, Any]] = Field(default=[], sa_type=JSONType())
    agent_id: str | None = Field(default=None)

class ChatService(Service[Chat]):
    @classmethod
    def model_class(cls) -> type[Chat]:
        return Chat

router = ChatService.router()
