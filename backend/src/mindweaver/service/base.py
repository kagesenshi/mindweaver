from mindweaver.fw.model import Base, NamedBase
from mindweaver.fw.service import Service, redefine_model
from sqlmodel import Field
from typing import TypeVar


class ProjectScopedBase(Base):
    """Base class for models that are scoped to a project."""

    project_id: int = Field(foreign_key="mw_project.id", index=True)


class ProjectScopedNamedBase(NamedBase):
    """Base class for named models that are scoped to a project."""

    project_id: int = Field(foreign_key="mw_project.id", index=True)


T = TypeVar("T", bound=ProjectScopedNamedBase)


class ProjectScopedService(Service[T]):
    """Base service for project-scoped models."""

    @classmethod
    def schema_class(cls) -> type[NamedBase]:
        """
        Override schema_class to exclude project_id from the schema used in forms/requests.
        """
        return redefine_model(
            f"{cls.model_class().__name__}Schema",
            cls.model_class(),
            exclude=["project_id"],
        )
