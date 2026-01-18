import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from io import BytesIO


def test_s3_upload(client: TestClient, test_project):
    # 1. Create S3 Storage
    resp = client.post(
        "/api/v1/s3_storages",
        json={
            "name": "test-s3",
            "title": "Test S3",
            "project_id": test_project["id"],
            "region": "us-east-1",
            "access_key": "test-access",
            "secret_key": "test-secret",
        },
    )
    assert resp.status_code == 200
    storage = resp.json()["record"]

    # 2. Mock boto3 and upload file
    with patch("boto3.client") as mock_boto:
        mock_s3 = MagicMock()
        mock_boto.return_value = mock_s3

        file_content = b"hello world"
        file_name = "test.txt"

        resp = client.post(
            f"/api/v1/s3_storages/{storage['id']}/_upload",
            params={"bucket": "test-bucket", "prefix": "test-prefix"},
            files={"file": (file_name, BytesIO(file_content), "text/plain")},
        )

        assert resp.status_code == 200
        assert resp.json()["status"] == "success"
        assert resp.json()["key"] == "test-prefix/test.txt"

        # Verify boto3 call
        mock_s3.upload_fileobj.assert_called_once()
        args, _ = mock_s3.upload_fileobj.call_args
        # args[1] is bucket, args[2] is key
        assert args[1] == "test-bucket"
        assert args[2] == "test-prefix/test.txt"


def test_s3_upload_no_prefix(client: TestClient, test_project):
    # 1. Create S3 Storage
    resp = client.post(
        "/api/v1/s3_storages",
        json={
            "name": "test-s3-no-prefix",
            "title": "Test S3 No Prefix",
            "project_id": test_project["id"],
            "region": "us-east-1",
            "access_key": "test-access",
            "secret_key": "test-secret",
        },
    )
    assert resp.status_code == 200
    storage = resp.json()["record"]

    # 2. Mock boto3 and upload file
    with patch("boto3.client") as mock_boto:
        mock_s3 = MagicMock()
        mock_boto.return_value = mock_s3

        file_content = b"hello world"
        file_name = "test.txt"

        resp = client.post(
            f"/api/v1/s3_storages/{storage['id']}/_upload",
            params={"bucket": "test-bucket", "prefix": ""},
            files={"file": (file_name, BytesIO(file_content), "text/plain")},
        )

        assert resp.status_code == 200
        assert resp.json()["status"] == "success"
        assert resp.json()["key"] == "test.txt"

        # Verify boto3 call
        mock_s3.upload_fileobj.assert_called_once()
        args, _ = mock_s3.upload_fileobj.call_args
        assert args[1] == "test-bucket"
        assert args[2] == "test.txt"
