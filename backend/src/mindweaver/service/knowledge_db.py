from . import NamedBase, Base
from . import Service
from sqlalchemy import String 
from sqlalchemy_utils import JSONType
from sqlmodel import Field, Relationship
from typing import Any


class KnowledgeDB(NamedBase, table=True):
    __tablename__ = 'mw_knowledge_db'
    type: str = Field(index=True)
    description: str = Field(default="", sa_type=String())
    parameters: dict[str, Any] = Field(sa_type=JSONType())

class KnowledgeDBService(Service[KnowledgeDB]):
    @classmethod
    def model_class(cls) -> type[KnowledgeDB]:
        return KnowledgeDB
    
router = KnowledgeDBService.router()