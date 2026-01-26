from fastapi.testclient import TestClient
import pytest
from unittest.mock import patch, Mock


def test_s3_storage_get_file(client: TestClient, test_project):
    """Test getting a file from s3 using _fs endpoint with action=get."""
    # Create a storage
    create_resp = client.post(
        "/api/v1/s3_storages",
        headers={"X-Project-Id": str(test_project["id"])},
        json={
            "name": "download-test-storage",
            "title": "Download Test Storage",
            "region": "us-east-1",
            "access_key": "AKIA...",
            "secret_key": "secret",
            "project_id": test_project["id"],
        },
    )
    assert create_resp.status_code == 200
    storage_id = create_resp.json()["data"]["id"]

    # Mock boto3 client
    with patch("boto3.client") as mock_s3:
        mock_client = mock_s3.return_value

        presigned_url = "http://fake-s3-presigned-url.com/file"
        mock_client.generate_presigned_url.return_value = presigned_url

        # Test 1: Default redirect behavior
        resp = client.get(
            f"/api/v1/s3_storages/{storage_id}/_fs?action=get&bucket=test-bucket&key=folder/test.txt",
            follow_redirects=False,
        )

        assert resp.status_code == 307
        assert resp.headers["location"] == presigned_url

        # Test 2: JSON response behavior (requested by frontend)
        resp = client.get(
            f"/api/v1/s3_storages/{storage_id}/_fs?action=get&bucket=test-bucket&key=folder/test.txt",
            headers={"Accept": "application/json"},
        )

        assert resp.status_code == 200
        assert resp.json()["url"] == presigned_url

        # Verify generate_presigned_url call
        mock_client.generate_presigned_url.assert_called_with(
            "get_object",
            Params={"Bucket": "test-bucket", "Key": "folder/test.txt"},
            ExpiresIn=3600,
        )
