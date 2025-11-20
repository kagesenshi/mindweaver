from . import NamedBase, Base
from . import Service
from sqlalchemy import String
from sqlalchemy_utils import JSONType
from sqlmodel import Field, Relationship
from typing import Any

class AIAgent(NamedBase, table=True):
    __tablename__ = 'mw_ai_agent'
    model: str = Field(default="gpt-4-turbo")
    temperature: float = Field(default=0.7)
    system_prompt: str = Field(default="")
    status: str = Field(default="Inactive")
    knowledge_db_ids: list[str] = Field(default=[], sa_type=JSONType())

class AIAgentService(Service[AIAgent]):
    @classmethod
    def model_class(cls) -> type[AIAgent]:
        return AIAgent

router = AIAgentService.router()
