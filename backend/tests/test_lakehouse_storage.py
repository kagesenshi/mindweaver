from fastapi.testclient import TestClient
import pytest


def test_lakehouse_storage_create_valid(client: TestClient, test_project):
    """Test creating a valid lakehouse storage."""
    resp = client.post(
        "/api/v1/lakehouse_storages",
        headers={"X-Project-Id": str(test_project["id"])},
        json={
            "name": "production-lakehouse",
            "title": "Production Lakehouse Storage",
            "parameters": {
                "bucket": "my-lakehouse-bucket",
                "region": "us-east-1",
                "access_key": "AKIAIOSFODNN7EXAMPLE",
                "secret_key": "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
            },
        },
    )

    if resp.status_code != 200:
        print(f"Error response: {resp.json()}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["record"]["name"] == "production-lakehouse"
    assert data["record"]["parameters"]["bucket"] == "my-lakehouse-bucket"
    assert data["record"]["parameters"]["region"] == "us-east-1"
    # Secret key should be encrypted
    assert (
        data["record"]["parameters"]["secret_key"]
        != "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"
    )


def test_lakehouse_storage_create_with_endpoint(client: TestClient, test_project):
    """Test creating lakehouse storage with custom endpoint."""
    resp = client.post(
        "/api/v1/lakehouse_storages",
        headers={"X-Project-Id": str(test_project["id"])},
        json={
            "name": "minio-lakehouse",
            "title": "MinIO Lakehouse Storage",
            "parameters": {
                "bucket": "minio-bucket",
                "region": "us-east-1",
                "access_key": "minioadmin",
                "secret_key": "minioadmin",
                "endpoint_url": "https://minio.example.com",
            },
        },
    )

    assert resp.status_code == 200
    data = resp.json()
    assert data["record"]["parameters"]["endpoint_url"] == "https://minio.example.com"


# ============================================================================
# S3 Configuration Validation Tests
# ============================================================================


def test_lakehouse_storage_invalid_bucket_empty(client: TestClient, test_project):
    """Test lakehouse storage with empty bucket name."""
    resp = client.post(
        "/api/v1/lakehouse_storages",
        headers={"X-Project-Id": str(test_project["id"])},
        json={
            "name": "invalid-storage",
            "title": "Invalid Storage",
            "parameters": {
                "bucket": "",
                "region": "us-east-1",
                "access_key": "AKIAIOSFODNN7EXAMPLE",
            },
        },
    )

    assert resp.status_code == 422
    error = resp.json()
    assert "detail" in error
    assert "bucket" in error["detail"].lower()


def test_lakehouse_storage_invalid_bucket_special_chars(
    client: TestClient, test_project
):
    """Test lakehouse storage with invalid bucket name (special characters)."""
    resp = client.post(
        "/api/v1/lakehouse_storages",
        headers={"X-Project-Id": str(test_project["id"])},
        json={
            "name": "invalid-storage",
            "title": "Invalid Storage",
            "parameters": {
                "bucket": "my_bucket@123!",
                "region": "us-east-1",
                "access_key": "AKIAIOSFODNN7EXAMPLE",
            },
        },
    )

    assert resp.status_code == 422
    error = resp.json()
    assert "detail" in error
    assert "bucket" in error["detail"].lower()


def test_lakehouse_storage_empty_region(client: TestClient, test_project):
    """Test lakehouse storage with empty region."""
    resp = client.post(
        "/api/v1/lakehouse_storages",
        headers={"X-Project-Id": str(test_project["id"])},
        json={
            "name": "invalid-storage",
            "title": "Invalid Storage",
            "parameters": {
                "bucket": "my-bucket",
                "region": "",
                "access_key": "AKIAIOSFODNN7EXAMPLE",
            },
        },
    )

    assert resp.status_code == 422
    error = resp.json()
    assert "detail" in error
    assert "region" in error["detail"].lower()


def test_lakehouse_storage_empty_access_key(client: TestClient, test_project):
    """Test lakehouse storage with empty access key."""
    resp = client.post(
        "/api/v1/lakehouse_storages",
        headers={"X-Project-Id": str(test_project["id"])},
        json={
            "name": "invalid-storage",
            "title": "Invalid Storage",
            "parameters": {
                "bucket": "my-bucket",
                "region": "us-east-1",
                "access_key": "",
            },
        },
    )

    assert resp.status_code == 422
    error = resp.json()
    assert "detail" in error
    assert "access_key" in error["detail"].lower()


def test_lakehouse_storage_invalid_endpoint_url(client: TestClient, test_project):
    """Test lakehouse storage with invalid endpoint URL."""
    resp = client.post(
        "/api/v1/lakehouse_storages",
        headers={"X-Project-Id": str(test_project["id"])},
        json={
            "name": "invalid-storage",
            "title": "Invalid Storage",
            "parameters": {
                "bucket": "my-bucket",
                "region": "us-east-1",
                "access_key": "AKIAIOSFODNN7EXAMPLE",
                "endpoint_url": "ftp://invalid-endpoint.com",
            },
        },
    )

    assert resp.status_code == 422
    error = resp.json()
    assert "detail" in error
    assert "endpoint" in error["detail"].lower()


# ============================================================================
# CRUD Operation Tests
# ============================================================================


def test_lakehouse_storage_list(client: TestClient, test_project):
    """Test listing lakehouse storages."""
    # Create a storage first
    client.post(
        "/api/v1/lakehouse_storages",
        headers={"X-Project-Id": str(test_project["id"])},
        json={
            "name": "test-storage",
            "title": "Test Storage",
            "parameters": {
                "bucket": "test-bucket",
                "region": "us-west-2",
                "access_key": "AKIAIOSFODNN7EXAMPLE",
            },
        },
    )

    # List storages
    resp = client.get(
        "/api/v1/lakehouse_storages", headers={"X-Project-Id": str(test_project["id"])}
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "records" in data
    assert len(data["records"]) > 0


def test_lakehouse_storage_get(client: TestClient, test_project):
    """Test getting a specific lakehouse storage."""
    # Create a storage
    create_resp = client.post(
        "/api/v1/lakehouse_storages",
        headers={"X-Project-Id": str(test_project["id"])},
        json={
            "name": "get-test-storage",
            "title": "Get Test Storage",
            "parameters": {
                "bucket": "get-test-bucket",
                "region": "eu-west-1",
                "access_key": "AKIAIOSFODNN7EXAMPLE",
            },
        },
    )
    assert create_resp.status_code == 200
    storage_id = create_resp.json()["record"]["id"]

    # Get the storage
    get_resp = client.get(f"/api/v1/lakehouse_storages/{storage_id}")
    assert get_resp.status_code == 200
    data = get_resp.json()
    assert data["record"]["name"] == "get-test-storage"


def test_lakehouse_storage_update(client: TestClient, test_project):
    """Test updating a lakehouse storage."""
    # Create a storage
    create_resp = client.post(
        "/api/v1/lakehouse_storages",
        headers={"X-Project-Id": str(test_project["id"])},
        json={
            "name": "update-test",
            "title": "Update Test",
            "parameters": {
                "bucket": "old-bucket",
                "region": "us-east-1",
                "access_key": "AKIAIOSFODNN7EXAMPLE",
                "secret_key": "old_secret",
            },
        },
    )
    assert create_resp.status_code == 200
    storage_id = create_resp.json()["record"]["id"]

    # Update the storage
    update_resp = client.put(
        f"/api/v1/lakehouse_storages/{storage_id}",
        headers={"X-Project-Id": str(test_project["id"])},
        json={
            "name": "update-test",
            "title": "Updated Test",
            "parameters": {
                "bucket": "new-bucket",
                "region": "us-west-2",
                "access_key": "AKIAIOSFODNN7EXAMPLE",
            },
        },
    )

    assert update_resp.status_code == 200
    data = update_resp.json()
    assert data["record"]["title"] == "Updated Test"
    assert data["record"]["parameters"]["bucket"] == "new-bucket"
    assert data["record"]["parameters"]["region"] == "us-west-2"


def test_lakehouse_storage_update_retain_secret(client: TestClient, test_project):
    """Test that updating without providing secret_key retains the existing one."""
    # Create a storage with secret
    create_resp = client.post(
        "/api/v1/lakehouse_storages",
        headers={"X-Project-Id": str(test_project["id"])},
        json={
            "name": "secret-test",
            "title": "Secret Test",
            "parameters": {
                "bucket": "secret-bucket",
                "region": "us-east-1",
                "access_key": "AKIAIOSFODNN7EXAMPLE",
                "secret_key": "original_secret_key",
            },
        },
    )
    assert create_resp.status_code == 200
    storage_id = create_resp.json()["record"]["id"]
    original_encrypted_secret = create_resp.json()["record"]["parameters"]["secret_key"]

    # Update without providing secret_key
    update_resp = client.put(
        f"/api/v1/lakehouse_storages/{storage_id}",
        headers={"X-Project-Id": str(test_project["id"])},
        json={
            "name": "secret-test",
            "title": "Secret Test Updated",
            "parameters": {
                "bucket": "secret-bucket",
                "region": "us-east-1",
                "access_key": "AKIAIOSFODNN7EXAMPLE",
            },
        },
    )

    assert update_resp.status_code == 200
    data = update_resp.json()
    # Secret should be retained (same encrypted value)
    assert data["record"]["parameters"]["secret_key"] == original_encrypted_secret


def test_lakehouse_storage_update_clear_secret(client: TestClient, test_project):
    """Test clearing secret_key using special marker."""
    # Create a storage with secret
    create_resp = client.post(
        "/api/v1/lakehouse_storages",
        headers={"X-Project-Id": str(test_project["id"])},
        json={
            "name": "clear-secret-test",
            "title": "Clear Secret Test",
            "parameters": {
                "bucket": "clear-bucket",
                "region": "us-east-1",
                "access_key": "AKIAIOSFODNN7EXAMPLE",
                "secret_key": "secret_to_clear",
            },
        },
    )
    assert create_resp.status_code == 200
    storage_id = create_resp.json()["record"]["id"]

    # Update with clear marker
    update_resp = client.put(
        f"/api/v1/lakehouse_storages/{storage_id}",
        headers={"X-Project-Id": str(test_project["id"])},
        json={
            "name": "clear-secret-test",
            "title": "Clear Secret Test",
            "parameters": {
                "bucket": "clear-bucket",
                "region": "us-east-1",
                "access_key": "AKIAIOSFODNN7EXAMPLE",
                "secret_key": "__CLEAR_SECRET_KEY__",
            },
        },
    )

    assert update_resp.status_code == 200
    data = update_resp.json()
    # Secret should be cleared
    assert data["record"]["parameters"]["secret_key"] == ""


def test_lakehouse_storage_delete(client: TestClient, test_project):
    """Test deleting a lakehouse storage."""
    # Create a storage
    create_resp = client.post(
        "/api/v1/lakehouse_storages",
        headers={"X-Project-Id": str(test_project["id"])},
        json={
            "name": "delete-test",
            "title": "Delete Test",
            "parameters": {
                "bucket": "delete-bucket",
                "region": "us-east-1",
                "access_key": "AKIAIOSFODNN7EXAMPLE",
            },
        },
    )
    assert create_resp.status_code == 200
    storage_id = create_resp.json()["record"]["id"]

    # Delete the storage
    delete_resp = client.delete(f"/api/v1/lakehouse_storages/{storage_id}")
    assert delete_resp.status_code == 200

    # Verify it's deleted
    get_resp = client.get(f"/api/v1/lakehouse_storages/{storage_id}")
    assert get_resp.status_code == 404


# ============================================================================
# Secret Key Encryption Tests
# ============================================================================


def test_lakehouse_storage_secret_key_encryption(client: TestClient, test_project):
    """Test that secret_key is encrypted when stored."""
    plain_secret = "my_super_secret_key_12345"

    resp = client.post(
        "/api/v1/lakehouse_storages",
        headers={"X-Project-Id": str(test_project["id"])},
        json={
            "name": "encryption-test",
            "title": "Encryption Test",
            "parameters": {
                "bucket": "encryption-bucket",
                "region": "us-east-1",
                "access_key": "AKIAIOSFODNN7EXAMPLE",
                "secret_key": plain_secret,
            },
        },
    )

    assert resp.status_code == 200
    data = resp.json()
    stored_secret = data["record"]["parameters"]["secret_key"]

    # Stored secret should not match plain text
    assert stored_secret != plain_secret
    # Stored secret should not be empty
    assert stored_secret != ""
    # Stored secret should be longer (encrypted)
    assert len(stored_secret) > len(plain_secret)


def test_lakehouse_storage_update_new_secret(client: TestClient, test_project):
    """Test updating with a new secret_key encrypts it."""
    # Create storage
    create_resp = client.post(
        "/api/v1/lakehouse_storages",
        headers={"X-Project-Id": str(test_project["id"])},
        json={
            "name": "new-secret-test",
            "title": "New Secret Test",
            "parameters": {
                "bucket": "new-secret-bucket",
                "region": "us-east-1",
                "access_key": "AKIAIOSFODNN7EXAMPLE",
                "secret_key": "old_secret",
            },
        },
    )
    assert create_resp.status_code == 200
    storage_id = create_resp.json()["record"]["id"]
    old_encrypted_secret = create_resp.json()["record"]["parameters"]["secret_key"]

    # Update with new secret
    new_secret = "brand_new_secret_key"
    update_resp = client.put(
        f"/api/v1/lakehouse_storages/{storage_id}",
        headers={"X-Project-Id": str(test_project["id"])},
        json={
            "name": "new-secret-test",
            "title": "New Secret Test",
            "parameters": {
                "bucket": "new-secret-bucket",
                "region": "us-east-1",
                "access_key": "AKIAIOSFODNN7EXAMPLE",
                "secret_key": new_secret,
            },
        },
    )

    assert update_resp.status_code == 200
    data = update_resp.json()
    new_encrypted_secret = data["record"]["parameters"]["secret_key"]

    # New encrypted secret should be different from old
    assert new_encrypted_secret != old_encrypted_secret
    # New encrypted secret should not be plain text
    assert new_encrypted_secret != new_secret


def test_list_lakehouse_storages_without_project_id_returns_empty(
    client: TestClient, test_project
):
    """Test that listing lakehouse storages without project_id returns empty list."""
    # Create a lakehouse storage in the project
    resp = client.post(
        "/api/v1/lakehouse_storages",
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
        headers={"X-Project-Id": str(test_project["id"])},
    )
    resp.raise_for_status()

    # List lakehouse storages WITHOUT project_id header
    # Should return empty list
    resp = client.get("/api/v1/lakehouse_storages")
    resp.raise_for_status()
    data = resp.json()

    assert data["records"] == []
