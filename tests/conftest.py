import pytest
import pytest_postgresql
from fastapi.testclient import TestClient
from mindweaver.app import app

@pytest.fixture(scope='session')
def client():
    return TestClient(app=app)
