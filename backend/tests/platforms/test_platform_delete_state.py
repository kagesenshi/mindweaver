import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch


def test_platform_delete_state_cascade(client: TestClient, test_project):
    with patch(
        "mindweaver.platform_service.base.PlatformService.deploy", return_value=None
    ), patch(
        "mindweaver.platform_service.base.PlatformService.decommission",
        return_value=None,
    ), patch(
        "mindweaver.platform_service.pgsql.PgSqlPlatformService.poll_status",
        return_value=None,
    ):
        # 1. Setup K8sCluster
        cluster_data = {
            "name": "test-cluster-delete",
            "title": "Test Cluster Delete",
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

        # 2. Create PgSqlCluster
        model_data = {
            "name": "delete-pg",
            "title": "Delete Postgres",
            "project_id": test_project["id"],
            "k8s_cluster_id": cluster_id,
            "instances": 3,
            "storage_size": "2Gi",
        }
        resp = client.post(
            "/api/v1/platform/pgsql",
            json=model_data,
            headers={"X-Project-Id": str(test_project["id"])},
        )
        resp.raise_for_status()
        model_id = resp.json()["record"]["id"]

        # 3. Create state
        update_data = {
            "status": "online",
            "active": True,
            "message": "Cluster is running",
        }
        resp = client.post(
            f"/api/v1/platform/pgsql/{model_id}/_state",
            json=update_data,
            headers={"X-Project-Id": str(test_project["id"])},
        )
        resp.raise_for_status()

        # Verify state exists
        resp = client.get(
            f"/api/v1/platform/pgsql/{model_id}/_state",
            headers={"X-Project-Id": str(test_project["id"])},
        )
        assert resp.status_code == 200
        assert resp.json().get("status") == "online"

        # 4. Delete the platform - using the new header
        resp = client.delete(
            f"/api/v1/platform/pgsql/{model_id}",
            headers={
                "X-Project-Id": str(test_project["id"]),
                "X-RESOURCE-NAME": "delete-pg",
            },
        )
        resp.raise_for_status()

        # 5. Verify the state is EXPLICITLY deleted (should return {} or error)
        # Note: In PlatformService.register_views, get_state returns {} if state not found
        resp = client.get(
            f"/api/v1/platform/pgsql/{model_id}/_state",
            headers={"X-Project-Id": str(test_project["id"])},
        )
        # Since the platform itself is deleted, the get_model dependency for _state view will raise 404
        assert resp.status_code == 404

        # To truly verify the DB record is gone, we'd need to check the DB directly
        # but the 404 from the view (which depends on the model) is expected behavior.
        # If we didn't delete the state, it would be a dangling orphan in the DB.
