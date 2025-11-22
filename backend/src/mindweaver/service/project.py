from . import NamedBase
from . import Service
from sqlmodel import Field


class Project(NamedBase, table=True):
    __tablename__ = "mw_project"
    description: str = Field(default="", nullable=True)


class ProjectService(Service[Project]):
    @classmethod
    def model_class(cls) -> type[Project]:
        return Project


router = ProjectService.router()
