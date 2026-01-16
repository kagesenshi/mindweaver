from fastapi.testclient import TestClient
from mindweaver.config import logger
import pytest


def test_datasource_basic(client: TestClient, test_project):
    """Test creating a valid data source with new schema."""
    resp = client.post(
        "/api/v1/data_sources",
        headers={"X-Project-Id": str(test_project["id"])},
        json={
            "name": "my-pg-db",
            "title": "My Postgres DB",
            "driver": "postgresql",
            "host": "localhost",
            "port": 5432,
            "login": "myuser",
            "password": "mypassword",
            "resource": "mydb",
            "project_id": test_project["id"],
        },
    )

    resp.raise_for_status()
    data = resp.json()
    record = data["record"]
    assert record["name"] == "my-pg-db"
    assert record["driver"] == "postgresql"
    assert record["host"] == "localhost"
    assert record["port"] == 5432
    assert record["resource"] == "mydb"


def test_datasource_create_form(client: TestClient, test_project):
    """Test that the _create-form endpoint returns valid schema."""
    resp = client.get(
        "/api/v1/data_sources/_create-form",
        headers={"X-Project-Id": str(test_project["id"])},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "record" in data
    assert "jsonschema" in data["record"]
    assert "widgets" in data["record"]
    # Verify new fields are present in properties
    props = data["record"]["jsonschema"]["properties"]
    assert "driver" in props
    assert "enable_ssl" in props
    assert "enable_ssl" in props
    assert "verify_ssl" in props
    assert data["record"]["widgets"]["password"]["type"] == "password"
    assert data["record"]["widgets"]["parameters"]["type"] == "key-value"


def test_datasource_web_source(client: TestClient, test_project):
    """Test creating a web source."""
    resp = client.post(
        "/api/v1/data_sources",
        headers={"X-Project-Id": str(test_project["id"])},
        json={
            "name": "web-source",
            "title": "My Web Source",
            "driver": "web",
            "host": "example.com",
            "enable_ssl": True,
            "verify_ssl": True,
            "resource": "/api/data",
            "project_id": test_project["id"],
        },
    )

    assert resp.status_code == 200
    record = resp.json()["record"]
    assert record["driver"] == "web"
    assert record["enable_ssl"] is True
    assert record["verify_ssl"] is True


def test_datasource_update(client: TestClient, test_project):
    """Test updating a data source."""
    # Create
    resp = client.post(
        "/api/v1/data_sources",
        headers={"X-Project-Id": str(test_project["id"])},
        json={
            "name": "update-test",
            "title": "Original Title",
            "driver": "mysql",
            "host": "localhost",
            "project_id": test_project["id"],
        },
    )
    source_id = resp.json()["record"]["id"]

    # Update
    resp = client.put(
        f"/api/v1/data_sources/{source_id}",
        headers={"X-Project-Id": str(test_project["id"])},
        json={
            "name": "update-test",  # Keep name or it might be immutable depending on base? NamedBase usually allows name update.
            "title": "Updated Title",
            "driver": "mysql",
            "verify_ssl": True,
            "project_id": test_project["id"],
        },
    )

    assert resp.status_code == 200
    record = resp.json()["record"]
    assert record["title"] == "Updated Title"
    assert record["verify_ssl"] is True


def test_delete_datasource(client: TestClient, test_project):
    # Create
    resp = client.post(
        "/api/v1/data_sources",
        headers={"X-Project-Id": str(test_project["id"])},
        json={
            "name": "delete-test",
            "title": "Delete Me",
            "driver": "postgresql",
            "project_id": test_project["id"],
        },
    )
    source_id = resp.json()["record"]["id"]

    # Delete
    resp = client.delete(
        f"/api/v1/data_sources/{source_id}",
        headers={"X-Project-Id": str(test_project["id"])},
    )
    assert resp.status_code == 200

    # Verify
    resp = client.get(
        f"/api/v1/data_sources/{source_id}",
        headers={"X-Project-Id": str(test_project["id"])},
    )
    assert resp.status_code == 404


def test_datasource_password_redaction(client: TestClient, test_project):
    """Test that password field is redacted in API responses."""
    # Create
    resp = client.post(
        "/api/v1/data_sources",
        headers={"X-Project-Id": str(test_project["id"])},
        json={
            "name": "redaction-check",
            "title": "Redaction Check",
            "driver": "postgresql",
            "host": "localhost",
            "password": "secret_password",
            "project_id": test_project["id"],
        },
    )
    assert resp.status_code == 200
    record = resp.json()["record"]
    assert record["password"] == "__REDACTED__"

    source_id = record["id"]

    # Get
    resp = client.get(
        f"/api/v1/data_sources/{source_id}",
        headers={"X-Project-Id": str(test_project["id"])},
    )
    assert resp.status_code == 200
    record = resp.json()["record"]
    assert record["password"] == "__REDACTED__"

    # List
    resp = client.get(
        "/api/v1/data_sources",
        headers={"X-Project-Id": str(test_project["id"])},
    )
    assert resp.status_code == 200
    records = resp.json()["records"]
    found = False
    for r in records:
        if r["id"] == source_id:
            assert r["password"] == "__REDACTED__"
            found = True
            break
    assert found
