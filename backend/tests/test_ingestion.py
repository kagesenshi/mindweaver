from fastapi.testclient import TestClient
import pytest


def test_create_ingestion_full_refresh(client: TestClient):
    """Test creating a full refresh ingestion."""
    # First create a data source
    ds_resp = client.post(
        "/data_sources",
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
        },
    )
    assert ds_resp.status_code == 200
    data_source_id = ds_resp.json()["record"]["id"]

    # Create a lakehouse storage
    ls_resp = client.post(
        "/lakehouse_storages",
        json={
            "name": "test-s3",
            "title": "Test S3 Storage",
            "parameters": {
                "bucket": "test-bucket",
                "region": "us-east-1",
                "access_key": "test-key",
                "secret_key": "test-secret",
            },
        },
    )
    assert ls_resp.status_code == 200
    lakehouse_storage_id = ls_resp.json()["record"]["id"]

    # Create ingestion
    resp = client.post(
        "/ingestions",
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
        },
    )

    assert resp.status_code == 200
    data = resp.json()
    assert data["record"]["name"] == "daily-users"
    assert data["record"]["ingestion_type"] == "full_refresh"
    assert data["record"]["config"]["table_name"] == "users"


def test_create_ingestion_incremental(client: TestClient):
    """Test creating an incremental ingestion with required fields."""
    # Create data source
    ds_resp = client.post(
        "/data_sources",
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
        },
    )
    assert ds_resp.status_code == 200
    data_source_id = ds_resp.json()["record"]["id"]

    # Create lakehouse storage
    ls_resp = client.post(
        "/lakehouse_storages",
        json={
            "name": "test-s3-inc",
            "title": "Test S3 Storage Inc",
            "parameters": {
                "bucket": "test-bucket-inc",
                "region": "us-east-1",
                "access_key": "test-key",
                "secret_key": "test-secret",
            },
        },
    )
    assert ls_resp.status_code == 200
    lakehouse_storage_id = ls_resp.json()["record"]["id"]

    # Create incremental ingestion
    resp = client.post(
        "/ingestions",
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
        },
    )

    assert resp.status_code == 200
    data = resp.json()
    assert data["record"]["name"] == "incremental-orders"
    assert data["record"]["ingestion_type"] == "incremental"
    assert data["record"]["config"]["primary_keys"] == ["order_id"]


def test_create_ingestion_incremental_missing_fields(client: TestClient):
    """Test that incremental ingestion fails without required fields."""
    # Create data source
    ds_resp = client.post(
        "/data_sources",
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
        },
    )
    assert ds_resp.status_code == 200
    data_source_id = ds_resp.json()["record"]["id"]

    # Create lakehouse storage
    ls_resp = client.post(
        "/lakehouse_storages",
        json={
            "name": "test-s3-fail",
            "title": "Test S3 Storage Fail",
            "parameters": {
                "bucket": "test-bucket-fail",
                "region": "us-east-1",
                "access_key": "test-key",
                "secret_key": "test-secret",
            },
        },
    )
    assert ls_resp.status_code == 200
    lakehouse_storage_id = ls_resp.json()["record"]["id"]

    # Try to create incremental ingestion without primary keys
    resp = client.post(
        "/ingestions",
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


def test_execute_ingestion(client: TestClient):
    """Test manual execution of an ingestion."""
    # Create data source
    ds_resp = client.post(
        "/data_sources",
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
        },
    )
    assert ds_resp.status_code == 200
    data_source_id = ds_resp.json()["record"]["id"]

    # Create lakehouse storage
    ls_resp = client.post(
        "/lakehouse_storages",
        json={
            "name": "test-s3-exec",
            "title": "Test S3 Storage Exec",
            "parameters": {
                "bucket": "test-bucket-exec",
                "region": "us-east-1",
                "access_key": "test-key",
                "secret_key": "test-secret",
            },
        },
    )
    assert ls_resp.status_code == 200
    lakehouse_storage_id = ls_resp.json()["record"]["id"]

    # Create ingestion
    ing_resp = client.post(
        "/ingestions",
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
        },
    )
    assert ing_resp.status_code == 200
    ingestion_id = ing_resp.json()["record"]["id"]

    # Execute the ingestion
    exec_resp = client.post(f"/ingestions/{ingestion_id}/execute")
    assert exec_resp.status_code == 200
    data = exec_resp.json()
    assert data["status"] == "success"
    assert "record" in data


def test_list_ingestion_runs(client: TestClient):
    """Test listing execution runs for an ingestion."""
    # Create data source
    ds_resp = client.post(
        "/data_sources",
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
        },
    )
    assert ds_resp.status_code == 200
    data_source_id = ds_resp.json()["record"]["id"]

    # Create lakehouse storage
    ls_resp = client.post(
        "/lakehouse_storages",
        json={
            "name": "test-s3-runs",
            "title": "Test S3 Storage Runs",
            "parameters": {
                "bucket": "test-bucket-runs",
                "region": "us-east-1",
                "access_key": "test-key",
                "secret_key": "test-secret",
            },
        },
    )
    assert ls_resp.status_code == 200
    lakehouse_storage_id = ls_resp.json()["record"]["id"]

    # Create ingestion
    ing_resp = client.post(
        "/ingestions",
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
        },
    )
    assert ing_resp.status_code == 200
    ingestion_id = ing_resp.json()["record"]["id"]

    # Execute the ingestion to create a run
    client.post(f"/ingestions/{ingestion_id}/execute")

    # List runs
    runs_resp = client.get(f"/ingestions/{ingestion_id}/runs")
    assert runs_resp.status_code == 200
    data = runs_resp.json()
    assert "records" in data
    assert len(data["records"]) > 0
    assert data["records"][0]["ingestion_id"] == ingestion_id
