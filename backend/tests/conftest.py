import pytest
import pytest_postgresql
from pytest_postgresql.executor import PostgreSQLExecutor
from psycopg.connection import Connection
from fastapi.testclient import TestClient
from mindweaver.app import app
from mindweaver.config import settings
from mindweaver.fw.service import Service
from mindweaver.fw.model import NamedBase
from sqlmodel import SQLModel, create_engine


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
def crud_client(postgresql_proc: PostgreSQLExecutor, postgresql: Connection):
    settings.db_host = postgresql_proc.host
    settings.db_port = postgresql_proc.port
    settings.db_name = postgresql_proc.dbname
    settings.db_user = postgresql_proc.user
    settings.db_pass = postgresql_proc.password

    class Model(NamedBase, table=True):
        __tablename__ = "crud_test"

    class ModelService(Service[Model]):

        @classmethod
        def model_class(cls):
            return Model

    router = ModelService.router()
    app.include_router(router)

    engine = create_engine(settings.db_uri)
    SQLModel.metadata.create_all(engine)
    yield TestClient(app=app)
    SQLModel.metadata.drop_all(engine)
