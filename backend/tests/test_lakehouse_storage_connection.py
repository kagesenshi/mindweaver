"""Tests for lakehouse storage test_connection endpoint."""

from fastapi.testclient import TestClient
import pytest
from unittest.mock import patch, MagicMock
from botocore.exceptions import ClientError, NoCredentialsError


@patch("mindweaver.service.lakehouse_storage.boto3")
def test_lakehouse_storage_test_connection_success(
    mock_boto3, client: TestClient, test_project
):
    """Test successful S3 connection test."""
    # Mock boto3 client
    mock_s3_client = MagicMock()
    mock_boto3.client.return_value = mock_s3_client
    mock_s3_client.head_bucket.return_value = {}

    # Create a storage first
    create_resp = client.post(
        "/lakehouse_storages",
        headers={"X-Project-Id": str(test_project["id"])},
        json={
            "name": "test-storage",
            "title": "Test Storage",
            "parameters": {
                "bucket": "test-bucket",
                "region": "us-east-1",
                "access_key": "AKIAIOSFODNN7EXAMPLE",
                "secret_key": "test_secret",
            },
        },
    )
    assert create_resp.status_code == 200

    # Test connection
    test_resp = client.post(
        "/lakehouse_storages/test_connection",
        json={
            "parameters": {
                "bucket": "test-bucket",
                "region": "us-east-1",
                "access_key": "AKIAIOSFODNN7EXAMPLE",
                "secret_key": "test_secret",
            }
        },
    )

    assert test_resp.status_code == 200
    data = test_resp.json()
    assert data["status"] == "success"
    assert "test-bucket" in data["message"]


def test_lakehouse_storage_test_connection_missing_bucket(client: TestClient):
    """Test connection with missing bucket name."""
    test_resp = client.post(
        "/lakehouse_storages/test_connection",
        json={
            "parameters": {
                "bucket": "",
                "region": "us-east-1",
                "access_key": "AKIAIOSFODNN7EXAMPLE",
            }
        },
    )

    assert test_resp.status_code == 400
    data = test_resp.json()
    assert "bucket" in data["detail"].lower()


def test_lakehouse_storage_test_connection_missing_region(client: TestClient):
    """Test connection with missing region."""
    test_resp = client.post(
        "/lakehouse_storages/test_connection",
        json={
            "parameters": {
                "bucket": "test-bucket",
                "region": "",
                "access_key": "AKIAIOSFODNN7EXAMPLE",
            }
        },
    )

    assert test_resp.status_code == 400
    data = test_resp.json()
    assert "region" in data["detail"].lower()


def test_lakehouse_storage_test_connection_missing_access_key(client: TestClient):
    """Test connection with missing access key."""
    test_resp = client.post(
        "/lakehouse_storages/test_connection",
        json={
            "parameters": {
                "bucket": "test-bucket",
                "region": "us-east-1",
                "access_key": "",
            }
        },
    )

    assert test_resp.status_code == 400
    data = test_resp.json()
    assert "access key" in data["detail"].lower()


@patch("mindweaver.service.lakehouse_storage.boto3")
def test_lakehouse_storage_test_connection_with_endpoint_url(
    mock_boto3, client: TestClient
):
    """Test connection with custom endpoint URL (MinIO, etc.)."""
    mock_s3_client = MagicMock()
    mock_boto3.client.return_value = mock_s3_client
    mock_s3_client.head_bucket.return_value = {}

    test_resp = client.post(
        "/lakehouse_storages/test_connection",
        json={
            "parameters": {
                "bucket": "minio-bucket",
                "region": "us-east-1",
                "access_key": "minioadmin",
                "secret_key": "minioadmin",
                "endpoint_url": "https://minio.example.com",
            }
        },
    )

    assert test_resp.status_code == 200
    data = test_resp.json()
    assert data["status"] == "success"

    # Verify boto3 was called with endpoint_url
    mock_boto3.client.assert_called_once()
    call_kwargs = mock_boto3.client.call_args[1]
    assert call_kwargs["endpoint_url"] == "https://minio.example.com"


@patch("mindweaver.service.lakehouse_storage.boto3")
def test_lakehouse_storage_test_connection_bucket_not_found(
    mock_boto3, client: TestClient
):
    """Test connection when bucket doesn't exist."""
    mock_s3_client = MagicMock()
    mock_boto3.client.return_value = mock_s3_client

    # Simulate bucket not found error
    error_response = {"Error": {"Code": "404", "Message": "Not Found"}}
    mock_s3_client.head_bucket.side_effect = ClientError(error_response, "HeadBucket")

    test_resp = client.post(
        "/lakehouse_storages/test_connection",
        json={
            "parameters": {
                "bucket": "nonexistent-bucket",
                "region": "us-east-1",
                "access_key": "AKIAIOSFODNN7EXAMPLE",
                "secret_key": "test_secret",
            }
        },
    )

    assert test_resp.status_code == 400
    data = test_resp.json()
    assert "not found" in data["detail"].lower()


@patch("mindweaver.service.lakehouse_storage.boto3")
def test_lakehouse_storage_test_connection_access_denied(
    mock_boto3, client: TestClient
):
    """Test connection when access is denied."""
    mock_s3_client = MagicMock()
    mock_boto3.client.return_value = mock_s3_client

    # Simulate access denied error
    error_response = {"Error": {"Code": "403", "Message": "Forbidden"}}
    mock_s3_client.head_bucket.side_effect = ClientError(error_response, "HeadBucket")

    test_resp = client.post(
        "/lakehouse_storages/test_connection",
        json={
            "parameters": {
                "bucket": "restricted-bucket",
                "region": "us-east-1",
                "access_key": "AKIAIOSFODNN7EXAMPLE",
                "secret_key": "test_secret",
            }
        },
    )

    assert test_resp.status_code == 400
    data = test_resp.json()
    assert "access denied" in data["detail"].lower()


@patch("mindweaver.service.lakehouse_storage.boto3")
def test_lakehouse_storage_test_connection_with_stored_secret(
    mock_boto3, client: TestClient, test_project
):
    """Test connection using stored encrypted secret key."""
    # Create a storage with secret key
    create_resp = client.post(
        "/lakehouse_storages",
        headers={"X-Project-Id": str(test_project["id"])},
        json={
            "name": "stored-secret-test",
            "title": "Stored Secret Test",
            "parameters": {
                "bucket": "test-bucket",
                "region": "us-east-1",
                "access_key": "AKIAIOSFODNN7EXAMPLE",
                "secret_key": "stored_secret_key",
            },
        },
    )
    assert create_resp.status_code == 200
    storage_id = create_resp.json()["record"]["id"]

    # Test connection without providing secret key (should use stored one)
    mock_s3_client = MagicMock()
    mock_boto3.client.return_value = mock_s3_client
    mock_s3_client.head_bucket.return_value = {}

    test_resp = client.post(
        "/lakehouse_storages/test_connection",
        headers={"X-Project-Id": str(test_project["id"])},
        json={
            "storage_id": storage_id,
            "parameters": {
                "bucket": "test-bucket",
                "region": "us-east-1",
                "access_key": "AKIAIOSFODNN7EXAMPLE",
                # No secret_key provided - should use stored one
            },
        },
    )

    assert test_resp.status_code == 200
    data = test_resp.json()
    assert data["status"] == "success"
