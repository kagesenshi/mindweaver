from . import NamedBase, Base
from .ontology import Ontology
from .base import ProjectScopedNamedBase, ProjectScopedService
from sqlalchemy import String
from sqlalchemy_utils import JSONType
from sqlmodel import Field, Relationship
from typing import Any, Optional, Literal

DBType = Literal[
    "passage-graph",
    "tree-graph",
    "knowledge-graph",
    "textual-knowledge-graph",
]


class KnowledgeDB(ProjectScopedNamedBase, table=True):
    __tablename__ = "mw_knowledge_db"
    type: DBType = Field(index=True, sa_type=String())
    description: str = Field(default="", sa_type=String())
    parameters: dict[str, Any] = Field(default_factory=dict, sa_type=JSONType())

    ontology_id: Optional[int] = Field(default=None, foreign_key="mw_ontology.id")
    ontology: Optional["Ontology"] = Relationship()


class KnowledgeDBService(ProjectScopedService[KnowledgeDB]):
    @classmethod
    def model_class(cls) -> type[KnowledgeDB]:
        return KnowledgeDB

    @classmethod
    def widgets(cls) -> dict[str, Any]:
        return {
            "type": {
                "type": "select",
                "options": [
                    {"value": "passage-graph", "label": "Passage Graph"},
                    {"value": "tree-graph", "label": "Tree Graph"},
                    {"value": "knowledge-graph", "label": "Knowledge Graph"},
                    {
                        "value": "textual-knowledge-graph",
                        "label": "Textual Knowledge Graph",
                    },
                ],
            }
        }

    @classmethod
    def internal_fields(cls) -> list[str]:
        return super().internal_fields() + ["parameters"]


router = KnowledgeDBService.router()
