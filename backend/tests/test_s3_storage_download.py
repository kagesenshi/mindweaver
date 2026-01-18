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
    storage_id = create_resp.json()["record"]["id"]

    # Mock boto3 client
    with patch("boto3.client") as mock_s3:
        mock_client = mock_s3.return_value

        # Mock get_object response
        import io

        file_content = b"fake s3 content"
        mock_client.get_object.return_value = {
            "Body": io.BytesIO(file_content),
            "ContentType": "text/plain",
        }

        resp = client.get(
            f"/api/v1/s3_storages/{storage_id}/_fs?action=get&bucket=test-bucket&key=folder/test.txt"
        )

        assert resp.status_code == 200
        assert resp.content == file_content
        assert resp.headers["content-disposition"] == 'attachment; filename="test.txt"'
        assert "text/plain" in resp.headers["content-type"]

        # Verify get_object call
        mock_client.get_object.assert_called_once_with(
            Bucket="test-bucket", Key="folder/test.txt"
        )
