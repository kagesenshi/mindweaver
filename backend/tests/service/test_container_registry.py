# SPDX-FileCopyrightText: Copyright © 2026 Mohd Izhar Firdaus Bin Ismail
# SPDX-License-Identifier: AGPLv3+

import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch, MagicMock


def test_container_registry_crud(client: TestClient, test_project):
    """Test standard CRUD operations for ContainerRegistry model."""
    # Create
    payload = {
        "name": "my-registry",
        "title": "My Registry",
        "url": "https://ghcr.io",
        "username": "my-user",
        "password": "my-password",
        "project_id": test_project["id"],
    }
    resp = client.post(
        "/api/v1/container_registries",
        json=payload,
        headers={"X-Project-ID": str(test_project["id"])}
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()["data"]
    assert data["name"] == "my-registry"
    assert data["password"] == "__REDACTED__"

    # Read/List
    resp = client.get(
        "/api/v1/container_registries",
        headers={"X-Project-ID": str(test_project["id"])}
    )
    assert resp.status_code == 200
    records = resp.json()["data"]
    assert len(records) > 0

    # Update
    update_payload = {
        "title": "My Updated Registry",
        "password": "__REDACTED__"
    }
    resp = client.put(
        f"/api/v1/container_registries/{data['id']}",
        json=update_payload,
        headers={"X-Project-ID": str(test_project["id"])}
    )
    assert resp.status_code == 200
    updated_data = resp.json()["data"]
    assert updated_data["title"] == "My Updated Registry"


@pytest.mark.asyncio
@patch("httpx.AsyncClient.get")
async def test_container_registry_test_connection_success(mock_get, client: TestClient, test_project):
    """Test successful connection check to Container Registry."""
    # Mock /v2/ returning 200 (auth not required or already authenticated)
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_get.return_value = mock_resp

    payload = {
        "url": "https://ghcr.io",
        "username": "user",
        "password": "pass",
    }
    resp = client.post(
        "/api/v1/container_registries/_test-connection",
        json=payload,
        headers={"X-Project-ID": str(test_project["id"])}
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["status"] == "success"


@pytest.mark.asyncio
@patch("httpx.AsyncClient.get")
async def test_container_registry_test_connection_failure(mock_get, client: TestClient, test_project):
    """Test failed connection check to Container Registry."""
    # Mock connection exception
    mock_get.side_effect = Exception("Connection refused")

    payload = {
        "url": "https://ghcr.io",
        "username": "user",
        "password": "pass",
    }
    resp = client.post(
        "/api/v1/container_registries/_test-connection",
        json=payload,
        headers={"X-Project-ID": str(test_project["id"])}
    )
    assert resp.status_code == 422, resp.text
    assert resp.json()["type"] == "validation_error"
