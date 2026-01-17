import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient
from mindweaver.platform_service.pgsql import PgSqlPlatformService


def test_refresh_missing_greenlet_error(client: TestClient, test_project):
    # setup k8s cluster
    cluster_data = {
        "name": "test-cluster-refresh",
        "title": "Test Cluster Refresh",
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

    # create platform
    model_data = {
        "name": "refresh-pg",
        "title": "Refresh Postgres",
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
    model_id = resp.json()["record"]["id"]

    # Mock poll_status to commit and expire everything
    async def mock_poll_status(self, model):
        await self.session.commit()

    with patch.object(
        PgSqlPlatformService, "poll_status", autospec=True, side_effect=mock_poll_status
    ):
        resp = client.post(
            f"/api/v1/platform/pgsql/{model_id}/_refresh",
            headers={"X-Project-Id": str(test_project["id"])},
        )
        # This is where it should fail if the bug exists
        assert resp.status_code == 200
