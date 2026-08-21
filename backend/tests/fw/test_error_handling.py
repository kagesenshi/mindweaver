# SPDX-FileCopyrightText: Copyright © 2026 Mohd Izhar Firdaus Bin Ismail
# SPDX-License-Identifier: AGPLv3+

from fastapi.testclient import TestClient
import pytest


def test_error_404_not_found(client: TestClient):
    """Test that 404 error follows the standardized structure."""
    resp = client.get("/api/v1/non-existent-endpoint")
    assert resp.status_code == 404
    data = resp.json()
    assert data["status"] == "error"
    assert data["type"] == "http_error"
    assert "detail" in data
    assert isinstance(data["detail"], str)


def test_error_422_validation(client: TestClient, test_project):
    """Test that 422 validation error follows the standardized structure."""
    # Try to create S3 storage with missing required fields
    resp = client.post(
        "/api/v1/s3_storages",
        headers={"X-Project-Id": str(test_project["id"])},
        json={
            "name": "invalid-s3",
            # missing title, region, access_key
        },
    )
    assert resp.status_code == 422
    data = resp.json()
    assert data["status"] == "error"
    assert data["type"] == "validation_error"
    assert "detail" in data
    assert isinstance(data["detail"], list)
    assert len(data["detail"]) > 0
    first_error = data["detail"][0]
    assert "msg" in first_error
    assert "type" in first_error
    assert "loc" in first_error
    assert isinstance(first_error["loc"], list)


def test_error_404_resource_not_found(client: TestClient, test_project):
    """Test that resource not found (custom exception) follows the standardized structure."""
    resp = client.get(
        "/api/v1/s3_storages/999999",
        headers={"X-Project-Id": str(test_project["id"])},
    )
    assert resp.status_code == 404
    data = resp.json()
    assert data["status"] == "error"
    assert data["type"] == "http_error"
    assert "detail" in data
    assert "S3Storage(999999)" in data["detail"]


from unittest.mock import patch

@patch("mindweaver.app.logger.exception")
@patch("mindweaver.fw.service.Service.get", side_effect=RuntimeError("Test traceback logging"))
def test_error_500_traceback_logged(mock_exists, mock_log_exception, client: TestClient, test_project):
    """Test that 500 internal server error logs a traceback."""
    local_client = TestClient(app=client.app, raise_server_exceptions=False)
    resp = local_client.get(
        "/api/v1/s3_storages/1",
        headers={"X-Project-Id": str(test_project["id"])},
    )
    assert resp.status_code == 500
    data = resp.json()
    assert data["status"] == "error"
    assert data["type"] == "server_error"
    assert "Test traceback logging" in data["detail"]
    mock_log_exception.assert_called_once()
    assert "An unexpected error occurred" in mock_log_exception.call_args[0][0]



