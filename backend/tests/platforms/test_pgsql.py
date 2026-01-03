import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient
from mindweaver.app import app
from mindweaver.platform_service.pgsql import PgSqlPlatformService


def test_pgsql_platform_crud(client: TestClient, test_project):
    # 1. Setup K8sCluster
    cluster_data = {
        "name": "test-cluster-pg",
        "title": "Test Cluster PG",
        "type": "remote",
        "kubeconfig": 'apiVersion: v1\nkind: Config\nclusters: []\ncontexts: []\ncurrent-context: ""\nusers: []',
        "project_id": test_project["id"],
    }
    resp = client.post(
        "/api/v1/k8s_clusters",
        json=cluster_data,
        headers={"X-Project-Id": str(test_project["id"])},
    )
    resp.raise_for_status()
    cluster_id = resp.json()["record"]["id"]

    # 1.1 Setup S3Storage
    s3_data = {
        "name": "test-s3",
        "title": "Test S3",
        "parameters": {
            "bucket": "my-bucket",
            "region": "us-east-1",
            "access_key": "my-access-key",
            "secret_key": "my-secret-key",
            "endpoint_url": "http://minio:9000",
        },
        "project_id": test_project["id"],
    }
    resp = client.post(
        "/api/v1/s3_storages",
        json=s3_data,
        headers={"X-Project-Id": str(test_project["id"])},
    )
    resp.raise_for_status()
    s3_id = resp.json()["record"]["id"]

    # 2. Create PgSqlCluster
    model_data = {
        "name": "my-pg",
        "title": "My Postgres",
        "project_id": test_project["id"],
        "k8s_cluster_id": cluster_id,
        "instances": 3,
        "storage_size": "2Gi",
        "backup_destination": "s3://my-bucket/backups",
        "s3_storage_id": s3_id,
        "enable_postgis": True,
    }
    resp = client.post(
        "/api/v1/platform/pgsql",
        json=model_data,
        headers={"X-Project-Id": str(test_project["id"])},
    )
    resp.raise_for_status()
    model_id = resp.json()["record"]["id"]
    assert resp.json()["record"]["s3_storage_id"] == s3_id
    assert resp.json()["record"]["instances"] == 3
    assert resp.json()["record"]["storage_size"] == "2Gi"

    # 3. Apply
    with patch("kubernetes.config.new_client_from_config") as mock_new_client, patch(
        "kubernetes.utils.create_from_yaml"
    ) as mock_create:

        resp = client.post(
            f"/api/v1/platform/pgsql/{model_id}/apply",
            headers={"X-Project-Id": str(test_project["id"])},
        )
        resp.raise_for_status()
        assert resp.json()["status"] == "success"

        # Verify kubernetes library was called
        mock_new_client.assert_called_once()
        mock_create.assert_called_once()

    # 4. Update
    update_data = {
        "title": "My Postgres Updated",
        "instances": 5,
        "storage_size": "2Gi",
        "k8s_cluster_id": cluster_id,
        "project_id": test_project["id"],
        "s3_storage_id": s3_id,
        "enable_citus": True,
    }
    resp = client.put(
        f"/api/v1/platform/pgsql/{model_id}",
        json=update_data,
        headers={"X-Project-Id": str(test_project["id"])},
    )
    resp.raise_for_status()
    assert resp.json()["record"]["instances"] == 5
    assert resp.json()["record"]["title"] == "My Postgres Updated"

    # 5. Delete
    resp = client.delete(
        f"/api/v1/platform/pgsql/{model_id}",
        headers={"X-Project-Id": str(test_project["id"])},
    )
    resp.raise_for_status()
