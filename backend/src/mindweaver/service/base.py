from mindweaver.fw.model import Base, NamedBase
from mindweaver.fw.service import Service, redefine_model
from sqlmodel import Field
from typing import TypeVar, Annotated
from fastapi import Header, Depends


class ProjectScopedBase(Base):
    """Base class for models that are scoped to a project."""

    project_id: int = Field(foreign_key="mw_project.id", index=True)


class ProjectScopedNamedBase(NamedBase):
    """Base class for named models that are scoped to a project."""

    project_id: int = Field(foreign_key="mw_project.id", index=True)


T = TypeVar("T", bound=ProjectScopedNamedBase)


async def x_project_id(x_project_id: Annotated[str | None, Header()] = None):
    pass


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
        )

    @classmethod
    def extra_dependencies(cls):
        return [Depends(x_project_id)]

    @classmethod
    def immutable_fields(cls) -> list[str]:
        return super().immutable_fields() + ["project_id"]
