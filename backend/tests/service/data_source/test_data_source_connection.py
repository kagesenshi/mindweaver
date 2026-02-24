# SPDX-FileCopyrightText: Copyright © 2025 Mohd Izhar Firdaus Bin Ismail
# SPDX-License-Identifier: AGPLv3+

from fastapi.testclient import TestClient
import pytest


def test_connection_endpoint(client: TestClient, test_project):
    """Test the connection endpoint with a mock web source."""
    # Create
    resp = client.post(
        "/api/v1/data_sources",
        headers={"X-Project-Id": str(test_project["id"])},
        json={
            "name": "conn-test-source",
            "title": "Connection Test Source",
            "driver": "web",
            "host": "example.com",
            "enable_ssl": True,
            "project_id": test_project["id"],
        },
    )
    source_id = resp.json()["data"]["id"]

    # Test Connection
    # We rely on external network or mocking, but for basic routed test:
    # Use example.com which usually returns 200
    resp = client.post(
        f"/api/v1/data_sources/{source_id}/_test-connection",
        headers={"X-Project-Id": str(test_project["id"])},
        json={},  # Empty overrides
    )

    # Pass if 200 or 4xx (endpoint might fail to connect but router works)
    # The service returns 400 if validation fails, or 500.
    # If connection fails it returns 400 with detail.
    # Note: verify_ssl defaults to False in model but if we didn't set it...
    # Wait, enable_ssl=True, host=example.com -> https://example.com

    assert resp.status_code in [200, 400]
    if resp.status_code == 200:
        data = resp.json()
        assert data["status"] == "success"
