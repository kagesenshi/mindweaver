import os

os.environ["MINDWEAVER_EXPERIMENTAL_AI_AGENT"] = "true"
os.environ["MINDWEAVER_EXPERIMENTAL_DATA_SOURCE"] = "true"
os.environ["MINDWEAVER_EXPERIMENTAL_KNOWLEDGE_DB"] = "true"
os.environ["MINDWEAVER_EXPERIMENTAL_LAKEHOUSE_STORAGE"] = "true"
os.environ["MINDWEAVER_EXPERIMENTAL_INGESTION"] = "true"
os.environ["MINDWEAVER_EXPERIMENTAL_CHAT"] = "true"

import pytest
import pytest_postgresql
from pytest_postgresql.executor import PostgreSQLExecutor
from psycopg.connection import Connection
from fastapi.testclient import TestClient
from mindweaver.fw.service import Service
from mindweaver.fw.model import NamedBase
from mindweaver.service.base import ProjectScopedNamedBase, ProjectScopedService
from sqlmodel import SQLModel, create_engine, Field
from mindweaver.config import settings


from mindweaver.app import app
from mindweaver.service.project import ProjectService


class Model(NamedBase, table=True):
    __tablename__ = "crud_test"


class ModelService(Service[Model]):

    @classmethod
    def model_class(cls):
        return Model


class ProjectScopedModel(ProjectScopedNamedBase, table=True):
    __tablename__ = "project_scoped_crud_test"


class ProjectScopedModelService(ProjectScopedService[ProjectScopedModel]):

    @classmethod
    def model_class(cls):
        return ProjectScopedModel


# Register routers at the module level
app.include_router(ModelService.router(), prefix="/api/v1")
app.include_router(ProjectService.router(), prefix="/api/v1")
app.include_router(ProjectScopedModelService.router(), prefix="/api/v1")


@pytest.fixture(scope="function")
def client(postgresql_proc: PostgreSQLExecutor, postgresql: Connection):
    settings.db_host = postgresql_proc.host
    settings.db_port = postgresql_proc.port
    settings.db_name = postgresql_proc.dbname
    settings.db_user = postgresql_proc.user
    settings.db_pass = postgresql_proc.password
    # Set a test encryption key for password encryption
    settings.fernet_key = "EFw4cCjDgHhGuZAGlwXmQhXg134ZdHjb9SeqcszWeSU="
    engine = create_engine(settings.db_uri)
    SQLModel.metadata.create_all(engine)
    yield TestClient(app=app)
    SQLModel.metadata.drop_all(engine)


@pytest.fixture(scope="function")
def test_project(client: TestClient):
    """Create a test project for use in tests."""
    response = client.post(
        "/api/v1/projects",
        json={
            "name": "test-project",
            "title": "Test Project",
            "description": "A test project for unit tests",
        },
    )
    assert response.status_code == 200
    return response.json()["record"]


@pytest.fixture(scope="function")
def crud_client(postgresql_proc: PostgreSQLExecutor, postgresql: Connection):
    settings.db_host = postgresql_proc.host
    settings.db_port = postgresql_proc.port
    settings.db_name = postgresql_proc.dbname
    settings.db_user = postgresql_proc.user
    settings.db_pass = postgresql_proc.password

    engine = create_engine(settings.db_uri)
    SQLModel.metadata.create_all(engine)
    yield TestClient(app=app)
    SQLModel.metadata.drop_all(engine)


@pytest.fixture(scope="function")
def project_scoped_crud_client(
    postgresql_proc: PostgreSQLExecutor, postgresql: Connection
):
    """Create a test client with a ProjectScopedNamedBase model for CRUD testing."""
    from mindweaver.service.project import ProjectService

    settings.db_host = postgresql_proc.host
    settings.db_port = postgresql_proc.port
    settings.db_name = postgresql_proc.dbname
    settings.db_user = postgresql_proc.user
    settings.db_pass = postgresql_proc.password
    # Set a test encryption key for password encryption
    settings.fernet_key = "EFw4cCjDgHhGuZAGlwXmQhXg134ZdHjb9SeqcszWeSU="

    engine = create_engine(settings.db_uri)
    SQLModel.metadata.create_all(engine)
    yield TestClient(app=app)
    SQLModel.metadata.drop_all(engine)
