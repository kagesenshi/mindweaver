# SPDX-FileCopyrightText: Copyright © 2025 Mohd Izhar Firdaus Bin Ismail
# SPDX-License-Identifier: AGPLv3+

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
    knowledge_db_ids: list[int] = Field(default=[], sa_type=JSONType())


class AIAgentService(ProjectScopedService[AIAgent]):
    @classmethod
    def model_class(cls) -> type[AIAgent]:
        return AIAgent

    @classmethod
    def widgets(cls) -> dict[str, Any]:
        return {
            "temperature": {
                "type": "range",
                "min": 0.0,
                "max": 1.0,
                "defaultValue": 0.7,
            },
            "knowledge_db_ids": {
                "label": "Knowledge DBs",
                "type": "relationship",
                "endpoint": "/api/v1/knowledge_dbs",
                "field": "id",
                "multiselect": True,
            },
        }


router = AIAgentService.router()
