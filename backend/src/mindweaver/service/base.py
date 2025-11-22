from mindweaver.fw.model import Base, NamedBase
from sqlmodel import Field


class ProjectScopedBase(Base):
    """Base class for models that are scoped to a project."""

    project_id: int = Field(foreign_key="mw_project.id", index=True)


class ProjectScopedNamedBase(NamedBase):
    """Base class for named models that are scoped to a project."""

    project_id: int = Field(foreign_key="mw_project.id", index=True)
