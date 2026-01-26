import pytest
from unittest.mock import patch, AsyncMock
from fastapi.testclient import TestClient
from mindweaver.platform_service.pgsql import PgSqlPlatform, PgSqlPlatformState


def test_pgsql_auto_deploy_on_update(client: TestClient, test_project):
    # 1. Setup K8sCluster
    cluster_data = {
        "name": "auto-deploy-cluster",
        "title": "Auto Deploy Cluster",
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
    cluster_id = resp.json()["data"]["id"]

    # 2. Create PgSqlPlatform
    model_data = {
        "name": "auto-pg",
        "title": "Auto Postgres",
        "project_id": test_project["id"],
        "k8s_cluster_id": cluster_id,
        "instances": 3,
        "storage_size": "1Gi",
    }
    resp = client.post(
        "/api/v1/platform/pgsql",
        json=model_data,
        headers={"X-Project-Id": str(test_project["id"])},
    )
    resp.raise_for_status()
    model_id = resp.json()["data"]["id"]

    with patch(
        "mindweaver.platform_service.pgsql.PgSqlPlatformService.deploy",
        new_callable=AsyncMock,
    ) as mock_deploy, patch(
        "mindweaver.platform_service.pgsql.PgSqlPlatformService.poll_status",
        new_callable=AsyncMock,
    ) as mock_poll_status:

        # 3. Mark as active in state (this triggers first deploy)
        resp = client.post(
            f"/api/v1/platform/pgsql/{model_id}/_state",
            json={"active": True},
            headers={"X-Project-Id": str(test_project["id"])},
        )
        resp.raise_for_status()
        assert mock_deploy.call_count == 1

        mock_deploy.reset_mock()
        mock_poll_status.reset_mock()

        # 4. Update the platform
        update_data = {
            "name": "auto-pg",
            "title": "Auto Postgres Updated",
            "project_id": test_project["id"],
            "k8s_cluster_id": cluster_id,
        }
        resp = client.put(
            f"/api/v1/platform/pgsql/{model_id}",
            json=update_data,
            headers={"X-Project-Id": str(test_project["id"])},
        )
        resp.raise_for_status()

        # Verify that deploy was called because it was active
        assert (
            mock_deploy.called
        ), "deploy() should have been called on update if active"
        assert (
            mock_poll_status.called
        ), "poll_status() should have been called after deploy"


def test_pgsql_auto_deploy_fail_raises_422(client: TestClient, test_project):
    # Setup
    cluster_data = {
        "name": "fail-deploy-cluster",
        "title": "Fail Deploy Cluster",
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
    cluster_id = resp.json()["data"]["id"]

    model_data = {
        "name": "fail-pg",
        "title": "Fail Postgres",
        "project_id": test_project["id"],
        "k8s_cluster_id": cluster_id,
    }
    resp = client.post(
        "/api/v1/platform/pgsql",
        json=model_data,
        headers={"X-Project-Id": str(test_project["id"])},
    )
    resp.raise_for_status()
    model_id = resp.json()["data"]["id"]

    with patch(
        "mindweaver.platform_service.pgsql.PgSqlPlatformService.deploy",
        new_callable=AsyncMock,
    ), patch(
        "mindweaver.platform_service.pgsql.PgSqlPlatformService.poll_status",
        new_callable=AsyncMock,
    ):
        # Set active=True
        client.post(
            f"/api/v1/platform/pgsql/{model_id}/_state",
            json={"active": True},
            headers={"X-Project-Id": str(test_project["id"])},
        )

    with patch(
        "mindweaver.platform_service.pgsql.PgSqlPlatformService.deploy",
        side_effect=RuntimeError("K8S Error"),
    ):
        update_data = {
            "name": "fail-pg",
            "title": "Fail Postgres Updated",
            "project_id": test_project["id"],
            "k8s_cluster_id": cluster_id,
        }
        resp = client.put(
            f"/api/v1/platform/pgsql/{model_id}",
            json=update_data,
            headers={"X-Project-Id": str(test_project["id"])},
        )
        assert resp.status_code == 422
        assert "K8S Error" in resp.json()["detail"][0]["msg"]
