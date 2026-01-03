from . import NamedBase, Base
from .base import ProjectScopedNamedBase, ProjectScopedService
from sqlalchemy import String
from sqlalchemy_utils import JSONType
from sqlmodel import Field, Relationship
from typing import Any, Optional


class AIAgent(ProjectScopedNamedBase, table=True):
    __tablename__ = "mw_ai_agent"
    model: str = Field(default="gpt-4-turbo")
    temperature: float = Field(default=0.7)
    system_prompt: str = Field(default="")
    status: str = Field(default="Inactive")
    knowledge_db_ids: list[str] = Field(default=[], sa_type=JSONType())


class AIAgentService(ProjectScopedService[AIAgent]):
    @classmethod
    def model_class(cls) -> type[AIAgent]:
        return AIAgent

    @classmethod
    def widgets(cls) -> dict[str, Any]:
        return {
            "knowledge_db_ids": {
                "type": "relationship",
                "endpoint": "/api/v1/knowledge_dbs",
                "field": "id",
                "multiselect": True,
            }
        }


router = AIAgentService.router()
