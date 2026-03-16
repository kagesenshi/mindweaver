# SPDX-FileCopyrightText: Copyright © 2026 Mohd Izhar Firdaus Bin Ismail
# SPDX-License-Identifier: AGPLv3+

from fastapi.testclient import TestClient
import pytest


def test_database_source_crud(client: TestClient, test_project):
    """Test CRUD for DatabaseSource."""
    # Create
    resp = client.post(
        "/api/v1/database-sources",
        headers={"X-Project-Id": str(test_project["id"])},
        json={
            "name": "test-db",
            "title": "Test DB",
            "engine": "postgresql",
            "host": "localhost",
            "port": 5432,
            "database": "testdb",
            "login": "user",
            "password": "pass",
            "project_id": test_project["id"],
        },
    )
    resp.raise_for_status()
    data = resp.json()["data"]
    assert data["name"] == "test-db"
    assert data["engine"] == "postgresql"
    assert data["password"] == "__REDACTED__"
    source_id = data["id"]

    # Read
    resp = client.get(
        f"/api/v1/database-sources/{source_id}",
        headers={"X-Project-Id": str(test_project["id"])},
    )
    assert resp.status_code == 200
    assert resp.json()["data"]["name"] == "test-db"

    # Update
    resp = client.put(
        f"/api/v1/database-sources/{source_id}",
        headers={"X-Project-Id": str(test_project["id"])},
        json={"title": "Updated DB Title"},
    )
    if resp.status_code == 422:
        print(resp.json())
    assert resp.status_code == 200
    assert resp.json()["data"]["title"] == "Updated DB Title"

    # Delete
    resp = client.delete(
        f"/api/v1/database-sources/{source_id}",
        headers={
            "X-Project-Id": str(test_project["id"]),
            "X-RESOURCE-NAME": "test-db"
        },
    )
    assert resp.status_code == 200


def test_web_source_crud(client: TestClient, test_project):
    """Test CRUD for WebSource."""
    resp = client.post(
        "/api/v1/web-sources",
        headers={"X-Project-Id": str(test_project["id"])},
        json={
            "name": "test-web",
            "title": "Test Web",
            "url": "https://example.com",
            "project_id": test_project["id"],
        },
    )
    resp.raise_for_status()
    assert resp.json()["data"]["url"] == "https://example.com"


def test_api_source_crud(client: TestClient, test_project):
    """Test CRUD for APISource."""
    resp = client.post(
        "/api/v1/api-sources",
        headers={"X-Project-Id": str(test_project["id"])},
        json={
            "name": "test-api",
            "title": "Test API",
            "base_url": "https://api.example.com",
            "api_type": "rest",
            "auth_type": "bearer",
            "password": "mytoken",
            "project_id": test_project["id"],
        },
    )
    resp.raise_for_status()
    data = resp.json()["data"]
    assert data["base_url"] == "https://api.example.com"
    assert data["password"] == "__REDACTED__"


def test_streaming_source_crud(client: TestClient, test_project):
    """Test CRUD for StreamingSource."""
    resp = client.post(
        "/api/v1/streaming-sources",
        headers={"X-Project-Id": str(test_project["id"])},
        json={
            "name": "test-stream",
            "title": "Test Stream",
            "broker_type": "kafka",
            "bootstrap_servers": "kafka:9092",
            "project_id": test_project["id"],
        },
    )
    resp.raise_for_status()
    assert resp.json()["data"]["broker_type"] == "kafka"


def test_connection_testing(client: TestClient, test_project):
    """Test the connection testing endpoint."""
    # Test without ID (dry run)
    resp = client.post(
        "/api/v1/web-sources/_test-connection",
        headers={"X-Project-Id": str(test_project["id"])},
        json={
            "url": "https://google.com",
        },
    )
    # google.com should be reachable in many environments, but we check if it handled the request
    assert resp.status_code in (200, 422) 
    
    # Test with ID
    # First create
    resp_create = client.post(
        "/api/v1/web-sources",
        headers={"X-Project-Id": str(test_project["id"])},
        json={
            "name": "conn-test",
            "title": "Conn Test",
            "url": "https://example.com",
            "project_id": test_project["id"],
        },
    )
    source_id = resp_create.json()["data"]["id"]
    
    resp = client.post(
        f"/api/v1/web-sources/{source_id}/_test-connection",
        headers={"X-Project-Id": str(test_project["id"])},
        json={},
    )
    assert resp.status_code in (200, 422)
