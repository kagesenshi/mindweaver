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

