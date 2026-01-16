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
