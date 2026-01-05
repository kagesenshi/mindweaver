"""Tests for s3 storage test_connection endpoint."""

from fastapi.testclient import TestClient
import pytest
from unittest.mock import patch, MagicMock
from botocore.exceptions import ClientError, NoCredentialsError


@patch("mindweaver.service.s3_storage.boto3")
def test_s3_storage_test_connection_success(
    mock_boto3, client: TestClient, test_project
):
    """Test successful S3 connection test."""
    # Mock boto3 client
    mock_s3_client = MagicMock()
    mock_boto3.client.return_value = mock_s3_client
    mock_s3_client.list_buckets.return_value = {}

    # Create a storage first
    create_resp = client.post(
        "/api/v1/s3_storages",
        headers={"X-Project-Id": str(test_project["id"])},
        json={
            "name": "test-storage",
            "title": "Test Storage",
            "region": "us-east-1",
            "access_key": "AKIAIOSFODNN7EXAMPLE",
            "secret_key": "test_secret",
            "project_id": test_project["id"],
        },
    )
    assert create_resp.status_code == 200

    # Test connection
    test_resp = client.post(
        "/api/v1/s3_storages/+test-connection",
        headers={"X-Project-Id": str(test_project["id"])},
        json={
            "region": "us-east-1",
            "access_key": "AKIAIOSFODNN7EXAMPLE",
            "secret_key": "test_secret",
            "project_id": test_project["id"],
        },
    )

    assert test_resp.status_code == 200
    data = test_resp.json()
    assert data["status"] == "success"
    assert "Successfully connected" in data["message"]


def test_s3_storage_test_connection_missing_region(client: TestClient, test_project):
    """Test connection with missing region."""
    test_resp = client.post(
        "/api/v1/s3_storages/+test-connection",
        headers={"X-Project-Id": str(test_project["id"])},
        json={
            "region": "",
            "access_key": "AKIAIOSFODNN7EXAMPLE",
            "project_id": test_project["id"],
        },
    )

    assert test_resp.status_code == 422
    data = test_resp.json()
    detail = data["detail"]
    detail_str = detail["msg"] if isinstance(detail, dict) else str(detail)
    assert "region" in detail_str.lower()


def test_s3_storage_test_connection_missing_access_key(
    client: TestClient, test_project
):
    """Test connection with missing access key."""
    test_resp = client.post(
        "/api/v1/s3_storages/+test-connection",
        headers={"X-Project-Id": str(test_project["id"])},
        json={
            "region": "us-east-1",
            "access_key": "",
            "project_id": test_project["id"],
        },
    )

    assert test_resp.status_code == 422
    data = test_resp.json()
    detail = data["detail"]
    detail_str = detail["msg"] if isinstance(detail, dict) else str(detail)
    assert "access key" in detail_str.lower()


@patch("mindweaver.service.s3_storage.boto3")
def test_s3_storage_test_connection_with_endpoint_url(
    mock_boto3, client: TestClient, test_project
):
    """Test connection with custom endpoint URL (MinIO, etc.)."""
    mock_s3_client = MagicMock()
    mock_boto3.client.return_value = mock_s3_client
    mock_s3_client.list_buckets.return_value = {}

    test_resp = client.post(
        "/api/v1/s3_storages/+test-connection",
        headers={"X-Project-Id": str(test_project["id"])},
        json={
            "region": "us-east-1",
            "access_key": "minioadmin",
            "secret_key": "minioadmin",
            "endpoint_url": "https://minio.example.com",
            "project_id": test_project["id"],
        },
    )

    assert test_resp.status_code == 200
    data = test_resp.json()
    assert data["status"] == "success"

    # Verify boto3 was called with endpoint_url
    mock_boto3.client.assert_called_once()
    call_kwargs = mock_boto3.client.call_args[1]
    assert call_kwargs["endpoint_url"] == "https://minio.example.com"


@patch("mindweaver.service.s3_storage.boto3")
def test_s3_storage_test_connection_access_denied(
    mock_boto3, client: TestClient, test_project
):
    """Test connection when access is denied."""
    mock_s3_client = MagicMock()
    mock_boto3.client.return_value = mock_s3_client

    # Simulate access denied error
    error_response = {"Error": {"Code": "403", "Message": "Forbidden"}}
    mock_s3_client.list_buckets.side_effect = ClientError(error_response, "ListBuckets")

    test_resp = client.post(
        "/api/v1/s3_storages/+test-connection",
        headers={"X-Project-Id": str(test_project["id"])},
        json={
            "region": "us-east-1",
            "access_key": "AKIAIOSFODNN7EXAMPLE",
            "secret_key": "test_secret",
            "project_id": test_project["id"],
        },
    )

    assert test_resp.status_code == 422
    data = test_resp.json()
    detail = data["detail"]
    detail_str = detail["msg"] if isinstance(detail, dict) else str(detail)
    assert "access denied" in detail_str.lower()


@patch("mindweaver.service.s3_storage.boto3")
def test_s3_storage_test_connection_with_stored_secret(
    mock_boto3, client: TestClient, test_project
):
    """Test connection using stored encrypted secret key."""
    # Create a storage with secret key
    create_resp = client.post(
        "/api/v1/s3_storages",
        headers={"X-Project-Id": str(test_project["id"])},
        json={
            "name": "stored-secret-test",
            "title": "Stored Secret Test",
            "region": "us-east-1",
            "access_key": "AKIAIOSFODNN7EXAMPLE",
            "secret_key": "stored_secret_key",
            "project_id": test_project["id"],
        },
    )
    assert create_resp.status_code == 200
    storage_id = create_resp.json()["record"]["id"]

    # Test connection without providing secret key (should use stored one)
    mock_s3_client = MagicMock()
    mock_boto3.client.return_value = mock_s3_client
    mock_s3_client.list_buckets.return_value = {}

    test_resp = client.post(
        "/api/v1/s3_storages/+test-connection",
        headers={"X-Project-Id": str(test_project["id"])},
        json={
            "storage_id": storage_id,
            "region": "us-east-1",
            "access_key": "AKIAIOSFODNN7EXAMPLE",
            # No secret_key provided - should use stored one
            "project_id": test_project["id"],
        },
    )

    assert test_resp.status_code == 200
    data = test_resp.json()
    assert data["status"] == "success"


@patch("mindweaver.service.s3_storage.boto3")
def test_s3_storage_test_connection_with_redacted_secret(
    mock_boto3, client: TestClient, test_project
):
    """Test connection using stored secret when REDACTED is sent."""
    # Create a storage with secret key
    create_resp = client.post(
        "/api/v1/s3_storages",
        headers={"X-Project-Id": str(test_project["id"])},
        json={
            "name": "redacted-secret-test",
            "title": "Redacted Secret Test",
            "region": "us-east-1",
            "access_key": "AKIAIOSFODNN7EXAMPLE",
            "secret_key": "redacted_stored_secret",
            "project_id": test_project["id"],
        },
    )
    assert create_resp.status_code == 200
    storage_id = create_resp.json()["record"]["id"]

    # Test connection with "__REDACTED__" secret key
    mock_s3_client = MagicMock()
    mock_boto3.client.return_value = mock_s3_client
    mock_s3_client.list_buckets.return_value = {}

    test_resp = client.post(
        "/api/v1/s3_storages/+test-connection",
        headers={"X-Project-Id": str(test_project["id"])},
        json={
            "storage_id": storage_id,
            "region": "us-east-1",
            "access_key": "AKIAIOSFODNN7EXAMPLE",
            "secret_key": "__REDACTED__",
            "project_id": test_project["id"],
        },
    )

    assert test_resp.status_code == 200
    data = test_resp.json()
    assert data["status"] == "success"

    # Verify boto3 was called with the ACTUAL stored secret, not REDACTED
    mock_boto3.client.assert_called_once()
    call_kwargs = mock_boto3.client.call_args[1]
    assert call_kwargs["aws_secret_access_key"] == "redacted_stored_secret"
