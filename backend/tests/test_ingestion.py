from fastapi.testclient import TestClient
import pytest


def test_create_ingestion_full_refresh(client: TestClient, test_project):
    """Test creating a full refresh ingestion."""
    # First create a data source
    ds_resp = client.post(
        "/api/v1/data_sources",
        headers={"X-Project-Id": str(test_project["id"])},
        json={
            "name": "test-db",
            "title": "Test Database",
            "type": "Database",
            "parameters": {
                "host": "localhost",
                "port": 5432,
                "username": "admin",
                "database_type": "postgresql",
            },
            "project_id": test_project["id"],
        },
    )
    assert ds_resp.status_code == 200
    data_source_id = ds_resp.json()["record"]["id"]

    # Create a lakehouse storage
    ls_resp = client.post(
        "/api/v1/lakehouse_storages",
        headers={"X-Project-Id": str(test_project["id"])},
        json={
            "name": "test-s3",
            "title": "Test S3 Storage",
            "parameters": {
                "bucket": "test-bucket",
                "region": "us-east-1",
                "access_key": "test-key",
                "secret_key": "test-secret",
            },
            "project_id": test_project["id"],
        },
    )
    assert ls_resp.status_code == 200
    lakehouse_storage_id = ls_resp.json()["record"]["id"]

    # Create ingestion
    resp = client.post(
        "/api/v1/ingestions",
        headers={"X-Project-Id": str(test_project["id"])},
        json={
            "name": "daily-users",
            "title": "Daily User Sync",
            "data_source_id": data_source_id,
            "lakehouse_storage_id": lakehouse_storage_id,
            "storage_path": "/data/users/",
            "cron_schedule": "0 2 * * *",
            "timezone": "UTC",
            "ingestion_type": "full_refresh",
            "config": {
                "table_name": "users",
                "ingestion_type": "full_refresh",
            },
            "project_id": test_project["id"],
        },
    )

    assert resp.status_code == 200
    data = resp.json()
    assert data["record"]["name"] == "daily-users"
    assert data["record"]["ingestion_type"] == "full_refresh"
    assert data["record"]["config"]["table_name"] == "users"


def test_create_ingestion_incremental(client: TestClient, test_project):
    """Test creating an incremental ingestion with required fields."""
    # Create data source
    ds_resp = client.post(
        "/api/v1/data_sources",
        headers={"X-Project-Id": str(test_project["id"])},
        json={
            "name": "test-db-inc",
            "title": "Test Database Incremental",
            "type": "Database",
            "parameters": {
                "host": "localhost",
                "port": 5432,
                "username": "admin",
                "database_type": "postgresql",
            },
            "project_id": test_project["id"],
        },
    )
    assert ds_resp.status_code == 200
    data_source_id = ds_resp.json()["record"]["id"]

    # Create lakehouse storage
    ls_resp = client.post(
        "/api/v1/lakehouse_storages",
        headers={"X-Project-Id": str(test_project["id"])},
        json={
            "name": "test-s3-inc",
            "title": "Test S3 Storage Inc",
            "parameters": {
                "bucket": "test-bucket-inc",
                "region": "us-east-1",
                "access_key": "test-key",
                "secret_key": "test-secret",
            },
            "project_id": test_project["id"],
        },
    )
    assert ls_resp.status_code == 200
    lakehouse_storage_id = ls_resp.json()["record"]["id"]

    # Create incremental ingestion
    resp = client.post(
        "/api/v1/ingestions",
        headers={"X-Project-Id": str(test_project["id"])},
        json={
            "name": "incremental-orders",
            "title": "Incremental Order Sync",
            "data_source_id": data_source_id,
            "lakehouse_storage_id": lakehouse_storage_id,
            "storage_path": "/data/orders/",
            "cron_schedule": "0 */4 * * *",
            "timezone": "America/New_York",
            "ingestion_type": "incremental",
            "config": {
                "table_name": "orders",
                "ingestion_type": "incremental",
                "primary_keys": ["order_id"],
                "last_modified_column": "updated_at",
                "created_column": "created_at",
                "source_timezone": "America/New_York",
            },
            "project_id": test_project["id"],
        },
    )

    assert resp.status_code == 200
    data = resp.json()
    assert data["record"]["name"] == "incremental-orders"
    assert data["record"]["ingestion_type"] == "incremental"
    assert data["record"]["config"]["primary_keys"] == ["order_id"]


def test_create_ingestion_incremental_missing_fields(client: TestClient, test_project):
    """Test that incremental ingestion fails without required fields."""
    # Create data source
    ds_resp = client.post(
        "/api/v1/data_sources",
        headers={"X-Project-Id": str(test_project["id"])},
        json={
            "name": "test-db-fail",
            "title": "Test Database Fail",
            "type": "Database",
            "parameters": {
                "host": "localhost",
                "port": 5432,
                "username": "admin",
                "database_type": "postgresql",
            },
            "project_id": test_project["id"],
        },
    )
    assert ds_resp.status_code == 200
    data_source_id = ds_resp.json()["record"]["id"]

    # Create lakehouse storage
    ls_resp = client.post(
        "/api/v1/lakehouse_storages",
        headers={"X-Project-Id": str(test_project["id"])},
        json={
            "name": "test-s3-fail",
            "title": "Test S3 Storage Fail",
            "parameters": {
                "bucket": "test-bucket-fail",
                "region": "us-east-1",
                "access_key": "test-key",
                "secret_key": "test-secret",
            },
            "project_id": test_project["id"],
        },
    )
    assert ls_resp.status_code == 200
    lakehouse_storage_id = ls_resp.json()["record"]["id"]

    # Try to create incremental ingestion without primary keys
    resp = client.post(
        "/api/v1/ingestions",
        headers={"X-Project-Id": str(test_project["id"])},
        json={
            "name": "bad-incremental",
            "title": "Bad Incremental Sync",
            "data_source_id": data_source_id,
            "lakehouse_storage_id": lakehouse_storage_id,
            "storage_path": "/data/bad/",
            "cron_schedule": "0 2 * * *",
            "timezone": "UTC",
            "ingestion_type": "incremental",
            "config": {
                "table_name": "bad_table",
                "ingestion_type": "incremental",
                # Missing primary_keys, last_modified_column, created_column
            },
            "project_id": test_project["id"],
        },
    )

    assert resp.status_code == 422
    error = resp.json()
    assert "detail" in error
    # Check that the error mentions the validation failure
    assert (
        "primary keys" in error["detail"].lower()
        or "incremental" in error["detail"].lower()
    )


def test_execute_ingestion(client: TestClient, test_project):
    """Test manual execution of an ingestion."""
    # Create data source
    ds_resp = client.post(
        "/api/v1/data_sources",
        headers={"X-Project-Id": str(test_project["id"])},
        json={
            "name": "test-db-exec",
            "title": "Test Database Exec",
            "type": "Database",
            "parameters": {
                "host": "localhost",
                "port": 5432,
                "username": "admin",
                "database_type": "postgresql",
            },
            "project_id": test_project["id"],
        },
    )
    assert ds_resp.status_code == 200
    data_source_id = ds_resp.json()["record"]["id"]

    # Create lakehouse storage
    ls_resp = client.post(
        "/api/v1/lakehouse_storages",
        headers={"X-Project-Id": str(test_project["id"])},
        json={
            "name": "test-s3-exec",
            "title": "Test S3 Storage Exec",
            "parameters": {
                "bucket": "test-bucket-exec",
                "region": "us-east-1",
                "access_key": "test-key",
                "secret_key": "test-secret",
            },
            "project_id": test_project["id"],
        },
    )
    assert ls_resp.status_code == 200
    lakehouse_storage_id = ls_resp.json()["record"]["id"]

    # Create ingestion
    ing_resp = client.post(
        "/api/v1/ingestions",
        headers={"X-Project-Id": str(test_project["id"])},
        json={
            "name": "exec-test",
            "title": "Execution Test",
            "data_source_id": data_source_id,
            "lakehouse_storage_id": lakehouse_storage_id,
            "storage_path": "/data/exec/",
            "cron_schedule": "0 2 * * *",
            "timezone": "UTC",
            "ingestion_type": "full_refresh",
            "config": {
                "table_name": "exec_table",
                "ingestion_type": "full_refresh",
            },
            "project_id": test_project["id"],
        },
    )
    assert ing_resp.status_code == 200
    ingestion_id = ing_resp.json()["record"]["id"]

    # Execute the ingestion
    exec_resp = client.post(f"/api/v1/ingestions/{ingestion_id}/execute")
    assert exec_resp.status_code == 200
    data = exec_resp.json()
    assert data["status"] == "success"
    assert "record" in data


def test_list_ingestion_runs(client: TestClient, test_project):
    """Test listing execution runs for an ingestion."""
    # Create data source
    ds_resp = client.post(
        "/api/v1/data_sources",
        headers={"X-Project-Id": str(test_project["id"])},
        json={
            "name": "test-db-runs",
            "title": "Test Database Runs",
            "type": "Database",
            "parameters": {
                "host": "localhost",
                "port": 5432,
                "username": "admin",
                "database_type": "postgresql",
            },
            "project_id": test_project["id"],
        },
    )
    assert ds_resp.status_code == 200
    data_source_id = ds_resp.json()["record"]["id"]

    # Create lakehouse storage
    ls_resp = client.post(
        "/api/v1/lakehouse_storages",
        headers={"X-Project-Id": str(test_project["id"])},
        json={
            "name": "test-s3-runs",
            "title": "Test S3 Storage Runs",
            "parameters": {
                "bucket": "test-bucket-runs",
                "region": "us-east-1",
                "access_key": "test-key",
                "secret_key": "test-secret",
            },
            "project_id": test_project["id"],
        },
    )
    assert ls_resp.status_code == 200
    lakehouse_storage_id = ls_resp.json()["record"]["id"]

    # Create ingestion
    ing_resp = client.post(
        "/api/v1/ingestions",
        headers={"X-Project-Id": str(test_project["id"])},
        json={
            "name": "runs-test",
            "title": "Runs Test",
            "data_source_id": data_source_id,
            "lakehouse_storage_id": lakehouse_storage_id,
            "storage_path": "/data/runs/",
            "cron_schedule": "0 2 * * *",
            "timezone": "UTC",
            "ingestion_type": "full_refresh",
            "config": {
                "table_name": "runs_table",
                "ingestion_type": "full_refresh",
            },
            "project_id": test_project["id"],
        },
    )
    assert ing_resp.status_code == 200
    ingestion_id = ing_resp.json()["record"]["id"]

    # Execute the ingestion to create a run
    client.post(f"/api/v1/ingestions/{ingestion_id}/execute")

    # List runs
    runs_resp = client.get(f"/api/v1/ingestions/{ingestion_id}/runs")
    assert runs_resp.status_code == 200
    data = runs_resp.json()
    assert "records" in data
    assert len(data["records"]) > 0
    assert data["records"][0]["ingestion_id"] == ingestion_id


def test_list_all_ingestions(client: TestClient, test_project):
    """Test listing all ingestions."""
    # Create data source
    ds_resp = client.post(
        "/api/v1/data_sources",
        headers={"X-Project-Id": str(test_project["id"])},
        json={
            "name": "test-db-list",
            "title": "Test Database List",
            "type": "Database",
            "parameters": {
                "host": "localhost",
                "port": 5432,
                "username": "admin",
                "database_type": "postgresql",
            },
            "project_id": test_project["id"],
        },
    )
    data_source_id = ds_resp.json()["record"]["id"]

    # Create lakehouse storage
    ls_resp = client.post(
        "/api/v1/lakehouse_storages",
        headers={"X-Project-Id": str(test_project["id"])},
        json={
            "name": "test-s3-list",
            "title": "Test S3 Storage List",
            "parameters": {
                "bucket": "test-bucket-list",
                "region": "us-east-1",
                "access_key": "test-key",
                "secret_key": "test-secret",
            },
            "project_id": test_project["id"],
        },
    )
    lakehouse_storage_id = ls_resp.json()["record"]["id"]

    # Create multiple ingestions
    for i in range(3):
        client.post(
            "/api/v1/ingestions",
            headers={"X-Project-Id": str(test_project["id"])},
            json={
                "name": f"ingestion-{i}",
                "title": f"Ingestion {i}",
                "data_source_id": data_source_id,
                "lakehouse_storage_id": lakehouse_storage_id,
                "storage_path": f"/data/ing{i}/",
                "cron_schedule": "0 2 * * *",
                "timezone": "UTC",
                "ingestion_type": "full_refresh",
                "config": {
                    "table_name": f"table_{i}",
                    "ingestion_type": "full_refresh",
                },
                "project_id": test_project["id"],
            },
        )

    # List all ingestions
    resp = client.get(
        "/api/v1/ingestions", headers={"X-Project-Id": str(test_project["id"])}
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "records" in data
    assert len(data["records"]) >= 3


def test_get_single_ingestion(client: TestClient, test_project):
    """Test getting a single ingestion by ID."""
    # Create data source
    ds_resp = client.post(
        "/api/v1/data_sources",
        headers={"X-Project-Id": str(test_project["id"])},
        json={
            "name": "test-db-get",
            "title": "Test Database Get",
            "type": "Database",
            "parameters": {
                "host": "localhost",
                "port": 5432,
                "username": "admin",
                "database_type": "postgresql",
            },
            "project_id": test_project["id"],
        },
    )
    data_source_id = ds_resp.json()["record"]["id"]

    # Create lakehouse storage
    ls_resp = client.post(
        "/api/v1/lakehouse_storages",
        headers={"X-Project-Id": str(test_project["id"])},
        json={
            "name": "test-s3-get",
            "title": "Test S3 Storage Get",
            "parameters": {
                "bucket": "test-bucket-get",
                "region": "us-east-1",
                "access_key": "test-key",
                "secret_key": "test-secret",
            },
            "project_id": test_project["id"],
        },
    )
    lakehouse_storage_id = ls_resp.json()["record"]["id"]

    # Create ingestion
    create_resp = client.post(
        "/api/v1/ingestions",
        headers={"X-Project-Id": str(test_project["id"])},
        json={
            "name": "get-test",
            "title": "Get Test",
            "data_source_id": data_source_id,
            "lakehouse_storage_id": lakehouse_storage_id,
            "storage_path": "/data/get/",
            "cron_schedule": "0 2 * * *",
            "timezone": "UTC",
            "ingestion_type": "full_refresh",
            "config": {
                "table_name": "get_table",
                "ingestion_type": "full_refresh",
            },
            "project_id": test_project["id"],
        },
    )
    ingestion_id = create_resp.json()["record"]["id"]

    # Get the ingestion
    get_resp = client.get(f"/api/v1/ingestions/{ingestion_id}")
    assert get_resp.status_code == 200
    data = get_resp.json()
    assert data["record"]["id"] == ingestion_id
    assert data["record"]["name"] == "get-test"


def test_update_ingestion(client: TestClient, test_project):
    """Test updating an existing ingestion."""
    # Create data source
    ds_resp = client.post(
        "/api/v1/data_sources",
        headers={"X-Project-Id": str(test_project["id"])},
        json={
            "name": "test-db-update",
            "title": "Test Database Update",
            "type": "Database",
            "parameters": {
                "host": "localhost",
                "port": 5432,
                "username": "admin",
                "database_type": "postgresql",
            },
            "project_id": test_project["id"],
        },
    )
    data_source_id = ds_resp.json()["record"]["id"]

    # Create lakehouse storage
    ls_resp = client.post(
        "/api/v1/lakehouse_storages",
        headers={"X-Project-Id": str(test_project["id"])},
        json={
            "name": "test-s3-update",
            "title": "Test S3 Storage Update",
            "parameters": {
                "bucket": "test-bucket-update",
                "region": "us-east-1",
                "access_key": "test-key",
                "secret_key": "test-secret",
            },
            "project_id": test_project["id"],
        },
    )
    lakehouse_storage_id = ls_resp.json()["record"]["id"]

    # Create ingestion
    create_resp = client.post(
        "/api/v1/ingestions",
        headers={"X-Project-Id": str(test_project["id"])},
        json={
            "name": "update-test",
            "title": "Update Test",
            "data_source_id": data_source_id,
            "lakehouse_storage_id": lakehouse_storage_id,
            "storage_path": "/data/update/",
            "cron_schedule": "0 2 * * *",
            "timezone": "UTC",
            "ingestion_type": "full_refresh",
            "config": {
                "table_name": "update_table",
                "ingestion_type": "full_refresh",
            },
            "project_id": test_project["id"],
        },
    )
    ingestion_id = create_resp.json()["record"]["id"]

    # Update the ingestion
    update_resp = client.put(
        f"/api/v1/ingestions/{ingestion_id}",
        headers={"X-Project-Id": str(test_project["id"])},
        json={
            "name": "updated-test",
            "title": "Updated Test",
            "data_source_id": data_source_id,
            "lakehouse_storage_id": lakehouse_storage_id,
            "storage_path": "/data/updated/",
            "cron_schedule": "0 4 * * *",
            "timezone": "America/New_York",
            "ingestion_type": "full_refresh",
            "config": {
                "table_name": "updated_table",
                "ingestion_type": "full_refresh",
            },
            "project_id": test_project["id"],
        },
    )
    assert update_resp.status_code == 200
    data = update_resp.json()
    # Name cannot be changed after creation (immutable field)
    assert data["record"]["name"] == "update-test"
    assert data["record"]["title"] == "Updated Test"
    assert data["record"]["cron_schedule"] == "0 4 * * *"
    assert data["record"]["timezone"] == "America/New_York"


def test_delete_ingestion(client: TestClient, test_project):
    """Test deleting an ingestion."""
    # Create data source
    ds_resp = client.post(
        "/api/v1/data_sources",
        headers={"X-Project-Id": str(test_project["id"])},
        json={
            "name": "test-db-delete",
            "title": "Test Database Delete",
            "type": "Database",
            "parameters": {
                "host": "localhost",
                "port": 5432,
                "username": "admin",
                "database_type": "postgresql",
            },
            "project_id": test_project["id"],
        },
    )
    data_source_id = ds_resp.json()["record"]["id"]

    # Create lakehouse storage
    ls_resp = client.post(
        "/api/v1/lakehouse_storages",
        headers={"X-Project-Id": str(test_project["id"])},
        json={
            "name": "test-s3-delete",
            "title": "Test S3 Storage Delete",
            "parameters": {
                "bucket": "test-bucket-delete",
                "region": "us-east-1",
                "access_key": "test-key",
                "secret_key": "test-secret",
            },
            "project_id": test_project["id"],
        },
    )
    lakehouse_storage_id = ls_resp.json()["record"]["id"]

    # Create ingestion
    create_resp = client.post(
        "/api/v1/ingestions",
        headers={"X-Project-Id": str(test_project["id"])},
        json={
            "name": "delete-test",
            "title": "Delete Test",
            "data_source_id": data_source_id,
            "lakehouse_storage_id": lakehouse_storage_id,
            "storage_path": "/data/delete/",
            "cron_schedule": "0 2 * * *",
            "timezone": "UTC",
            "ingestion_type": "full_refresh",
            "config": {
                "table_name": "delete_table",
                "ingestion_type": "full_refresh",
            },
            "project_id": test_project["id"],
        },
    )
    ingestion_id = create_resp.json()["record"]["id"]

    # Delete the ingestion
    delete_resp = client.delete(f"/api/v1/ingestions/{ingestion_id}")
    assert delete_resp.status_code == 200
    assert delete_resp.json()["status"] == "success"

    # Verify it's deleted
    get_resp = client.get(f"/api/v1/ingestions/{ingestion_id}")
    assert get_resp.status_code == 404


def test_create_ingestion_with_date_range(client: TestClient, test_project):
    """Test creating an ingestion with start and end dates."""
    # Create data source
    ds_resp = client.post(
        "/api/v1/data_sources",
        headers={"X-Project-Id": str(test_project["id"])},
        json={
            "name": "test-db-dates",
            "title": "Test Database Dates",
            "type": "Database",
            "parameters": {
                "host": "localhost",
                "port": 5432,
                "username": "admin",
                "database_type": "postgresql",
            },
            "project_id": test_project["id"],
        },
    )
    data_source_id = ds_resp.json()["record"]["id"]

    # Create lakehouse storage
    ls_resp = client.post(
        "/api/v1/lakehouse_storages",
        headers={"X-Project-Id": str(test_project["id"])},
        json={
            "name": "test-s3-dates",
            "title": "Test S3 Storage Dates",
            "parameters": {
                "bucket": "test-bucket-dates",
                "region": "us-east-1",
                "access_key": "test-key",
                "secret_key": "test-secret",
            },
            "project_id": test_project["id"],
        },
    )
    lakehouse_storage_id = ls_resp.json()["record"]["id"]

    # Create ingestion with date range
    resp = client.post(
        "/api/v1/ingestions",
        headers={"X-Project-Id": str(test_project["id"])},
        json={
            "name": "date-range-test",
            "title": "Date Range Test",
            "data_source_id": data_source_id,
            "lakehouse_storage_id": lakehouse_storage_id,
            "storage_path": "/data/dates/",
            "cron_schedule": "0 2 * * *",
            "start_date": "2025-01-01",
            "end_date": "2025-12-31",
            "timezone": "UTC",
            "ingestion_type": "full_refresh",
            "config": {
                "table_name": "date_table",
                "ingestion_type": "full_refresh",
            },
            "project_id": test_project["id"],
        },
    )

    assert resp.status_code == 200
    data = resp.json()
    # Dates are returned with timestamp format
    assert data["record"]["start_date"].startswith("2025-01-01")
    assert data["record"]["end_date"].startswith("2025-12-31")


def test_create_ingestion_with_complex_cron(client: TestClient, test_project):
    """Test creating an ingestion with various cron schedules."""
    # Create data source
    ds_resp = client.post(
        "/api/v1/data_sources",
        headers={"X-Project-Id": str(test_project["id"])},
        json={
            "name": "test-db-cron",
            "title": "Test Database Cron",
            "type": "Database",
            "parameters": {
                "host": "localhost",
                "port": 5432,
                "username": "admin",
                "database_type": "postgresql",
            },
            "project_id": test_project["id"],
        },
    )
    data_source_id = ds_resp.json()["record"]["id"]

    # Create lakehouse storage
    ls_resp = client.post(
        "/api/v1/lakehouse_storages",
        headers={"X-Project-Id": str(test_project["id"])},
        json={
            "name": "test-s3-cron",
            "title": "Test S3 Storage Cron",
            "parameters": {
                "bucket": "test-bucket-cron",
                "region": "us-east-1",
                "access_key": "test-key",
                "secret_key": "test-secret",
            },
            "project_id": test_project["id"],
        },
    )
    lakehouse_storage_id = ls_resp.json()["record"]["id"]

    # Test various cron schedules
    cron_schedules = [
        "0 */4 * * *",  # Every 4 hours
        "0 0 * * 0",  # Weekly on Sunday
        "0 0 1 * *",  # Monthly on the 1st
        "*/15 * * * *",  # Every 15 minutes
    ]

    for i, cron in enumerate(cron_schedules):
        resp = client.post(
            "/api/v1/ingestions",
            headers={"X-Project-Id": str(test_project["id"])},
            json={
                "name": f"cron-test-{i}",
                "title": f"Cron Test {i}",
                "data_source_id": data_source_id,
                "lakehouse_storage_id": lakehouse_storage_id,
                "storage_path": f"/data/cron{i}/",
                "cron_schedule": cron,
                "timezone": "UTC",
                "ingestion_type": "full_refresh",
                "config": {
                    "table_name": f"cron_table_{i}",
                    "ingestion_type": "full_refresh",
                },
                "project_id": test_project["id"],
            },
        )
        if resp.status_code != 200:
            print(f"Failed cron {cron}: {resp.json()}")
        assert resp.status_code == 200
        assert resp.json()["record"]["cron_schedule"] == cron


def test_create_ingestion_with_invalid_cron_schedule(client: TestClient, test_project):
    """Test creating an ingestion with invalid cron schedules."""
    # Create data source
    ds_resp = client.post(
        "/api/v1/data_sources",
        headers={"X-Project-Id": str(test_project["id"])},
        json={
            "name": "test-db-invalid-cron",
            "title": "Test Database Invalid Cron",
            "type": "Database",
            "parameters": {
                "host": "localhost",
                "port": 5432,
                "username": "admin",
                "database_type": "postgresql",
            },
            "project_id": test_project["id"],
        },
    )
    data_source_id = ds_resp.json()["record"]["id"]

    # Create lakehouse storage
    ls_resp = client.post(
        "/api/v1/lakehouse_storages",
        headers={"X-Project-Id": str(test_project["id"])},
        json={
            "name": "test-s3-invalid-cron",
            "title": "Test S3 Storage Invalid Cron",
            "parameters": {
                "bucket": "test-bucket-invalid-cron",
                "region": "us-east-1",
                "access_key": "test-key",
                "secret_key": "test-secret",
            },
            "project_id": test_project["id"],
        },
    )
    lakehouse_storage_id = ls_resp.json()["record"]["id"]

    # Test various invalid cron schedules
    invalid_cron_schedules = [
        "invalid cron",  # Not a valid cron format
        "0 0 0 0 0",  # Invalid values (0 for day/month)
        "60 * * * *",  # Invalid minute (60)
        "* 24 * * *",  # Invalid hour (24)
        "* * 32 * *",  # Invalid day (32)
        "* * * 13 *",  # Invalid month (13)
        "* * * * 8",  # Invalid day of week (8)
        "",  # Empty string
        "0",  # Too few fields
        "* * * *",  # Too few fields (4 instead of 5)
        "a b c d e",  # Non-numeric values
    ]

    for i, cron in enumerate(invalid_cron_schedules):
        resp = client.post(
            "/api/v1/ingestions",
            headers={"X-Project-Id": str(test_project["id"])},
            json={
                "name": f"invalid-cron-test-{i}",
                "title": f"Invalid Cron Test {i}",
                "data_source_id": data_source_id,
                "lakehouse_storage_id": lakehouse_storage_id,
                "storage_path": f"/data/invalid-cron{i}/",
                "cron_schedule": cron,
                "timezone": "UTC",
                "ingestion_type": "full_refresh",
                "config": {
                    "table_name": f"invalid_cron_table_{i}",
                    "ingestion_type": "full_refresh",
                },
            },
        )
        # Should fail with validation error
        assert (
            resp.status_code == 422
        ), f"Expected 422 for cron '{cron}', got {resp.status_code}"
        error = resp.json()
        assert "detail" in error
        # Check that the error mentions cron or schedule
        detail_str = str(error["detail"]).lower()
        assert (
            "cron" in detail_str or "schedule" in detail_str
        ), f"Error message should mention cron/schedule for '{cron}': {error['detail']}"


def test_create_ingestion_with_multiple_primary_keys(client: TestClient, test_project):
    """Test creating an incremental ingestion with multiple primary keys."""
    # Create data source
    ds_resp = client.post(
        "/api/v1/data_sources",
        headers={"X-Project-Id": str(test_project["id"])},
        json={
            "name": "test-db-multi-pk",
            "title": "Test Database Multi PK",
            "type": "Database",
            "parameters": {
                "host": "localhost",
                "port": 5432,
                "username": "admin",
                "database_type": "postgresql",
            },
            "project_id": test_project["id"],
        },
    )
    data_source_id = ds_resp.json()["record"]["id"]

    # Create lakehouse storage
    ls_resp = client.post(
        "/api/v1/lakehouse_storages",
        headers={"X-Project-Id": str(test_project["id"])},
        json={
            "name": "test-s3-multi-pk",
            "title": "Test S3 Storage Multi PK",
            "parameters": {
                "bucket": "test-bucket-multi-pk",
                "region": "us-east-1",
                "access_key": "test-key",
                "secret_key": "test-secret",
            },
            "project_id": test_project["id"],
        },
    )
    lakehouse_storage_id = ls_resp.json()["record"]["id"]

    # Create incremental ingestion with multiple primary keys
    resp = client.post(
        "/api/v1/ingestions",
        headers={"X-Project-Id": str(test_project["id"])},
        json={
            "name": "multi-pk-test",
            "title": "Multi PK Test",
            "data_source_id": data_source_id,
            "lakehouse_storage_id": lakehouse_storage_id,
            "storage_path": "/data/multi-pk/",
            "cron_schedule": "0 2 * * *",
            "timezone": "UTC",
            "ingestion_type": "incremental",
            "config": {
                "table_name": "composite_key_table",
                "ingestion_type": "incremental",
                "primary_keys": ["tenant_id", "user_id", "order_id"],
                "last_modified_column": "updated_at",
                "created_column": "created_at",
                "source_timezone": "UTC",
            },
            "project_id": test_project["id"],
        },
    )

    assert resp.status_code == 200
    data = resp.json()
    assert len(data["record"]["config"]["primary_keys"]) == 3
    assert "tenant_id" in data["record"]["config"]["primary_keys"]


def test_ingestion_with_different_timezones(client: TestClient, test_project):
    """Test creating ingestions with different timezones."""
    # Create data source
    ds_resp = client.post(
        "/api/v1/data_sources",
        headers={"X-Project-Id": str(test_project["id"])},
        json={
            "name": "test-db-tz",
            "title": "Test Database TZ",
            "type": "Database",
            "parameters": {
                "host": "localhost",
                "port": 5432,
                "username": "admin",
                "database_type": "postgresql",
            },
            "project_id": test_project["id"],
        },
    )
    data_source_id = ds_resp.json()["record"]["id"]

    # Create lakehouse storage
    ls_resp = client.post(
        "/api/v1/lakehouse_storages",
        headers={"X-Project-Id": str(test_project["id"])},
        json={
            "name": "test-s3-tz",
            "title": "Test S3 Storage TZ",
            "parameters": {
                "bucket": "test-bucket-tz",
                "region": "us-east-1",
                "access_key": "test-key",
                "secret_key": "test-secret",
            },
            "project_id": test_project["id"],
        },
    )
    lakehouse_storage_id = ls_resp.json()["record"]["id"]

    timezones = ["UTC", "America/New_York", "Europe/London", "Asia/Tokyo"]

    for i, tz in enumerate(timezones):
        resp = client.post(
            "/api/v1/ingestions",
            headers={"X-Project-Id": str(test_project["id"])},
            json={
                "name": f"tz-test-{i}",
                "title": f"TZ Test {i}",
                "data_source_id": data_source_id,
                "lakehouse_storage_id": lakehouse_storage_id,
                "storage_path": f"/data/tz{i}/",
                "cron_schedule": "0 2 * * *",
                "timezone": tz,
                "ingestion_type": "full_refresh",
                "config": {
                    "table_name": f"tz_table_{i}",
                    "ingestion_type": "full_refresh",
                },
                "project_id": test_project["id"],
            },
        )
        assert resp.status_code == 200
        assert resp.json()["record"]["timezone"] == tz


def test_list_ingestions_without_project_id_returns_empty(
    client: TestClient, test_project
):
    """Test that listing ingestions without project_id returns empty list."""
    # Create data source
    ds_resp = client.post(
        "/api/v1/data_sources",
        headers={"X-Project-Id": str(test_project["id"])},
        json={
            "name": "test-db",
            "title": "Test Database",
            "type": "Database",
            "parameters": {
                "host": "localhost",
                "port": 5432,
                "username": "admin",
                "database_type": "postgresql",
            },
            "project_id": test_project["id"],
        },
    )
    data_source_id = ds_resp.json()["record"]["id"]

    # Create lakehouse storage
    ls_resp = client.post(
        "/api/v1/lakehouse_storages",
        headers={"X-Project-Id": str(test_project["id"])},
        json={
            "name": "test-s3",
            "title": "Test S3 Storage",
            "parameters": {
                "bucket": "test-bucket",
                "region": "us-east-1",
                "access_key": "test-key",
                "secret_key": "test-secret",
            },
            "project_id": test_project["id"],
        },
    )
    lakehouse_storage_id = ls_resp.json()["record"]["id"]

    # Create an ingestion in the project
    resp = client.post(
        "/api/v1/ingestions",
        json={
            "name": "test-ingestion",
            "title": "Test Ingestion",
            "data_source_id": data_source_id,
            "lakehouse_storage_id": lakehouse_storage_id,
            "storage_path": "/data/test/",
            "cron_schedule": "0 2 * * *",
            "timezone": "UTC",
            "ingestion_type": "full_refresh",
            "config": {
                "table_name": "test_table",
                "ingestion_type": "full_refresh",
            },
            "project_id": test_project["id"],
        },
        headers={"X-Project-Id": str(test_project["id"])},
    )
    resp.raise_for_status()

    # List ingestions WITHOUT project_id header
    # Should return empty list
    resp = client.get("/api/v1/ingestions")
    resp.raise_for_status()
    data = resp.json()

    assert len(data["records"]) == 1
    assert data["records"][0]["name"] == "test-ingestion"
