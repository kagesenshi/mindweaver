from . import NamedBase, Base
from . import Service
from sqlalchemy import String 
from sqlalchemy_utils import JSONType
from sqlmodel import Field, Relationship
from typing import Any

class DataSource(NamedBase, table=True):
    __tablename__ = 'mw_datasource'
    type: str = Field(index=True)
    parameters: dict[str, Any] = Field(sa_type=JSONType())

class DataSourceService(Service[DataSource]):

    @classmethod
    def model_class(cls) -> type[DataSource]:
        return DataSource
    
router = DataSourceService.router()