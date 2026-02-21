import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch


def test_decommission_safety_header_required(client: TestClient, test_project):
    with patch(
        "mindweaver.platform_service.base.PlatformService._deploy_to_cluster"
    ), patch(
        "mindweaver.platform_service.base.PlatformService._decommission_from_cluster"
    ), patch(
        "mindweaver.platform_service.pgsql.PgSqlPlatformService.poll_status"
    ):

        # 1. Update project with K8s info
        project_update = {
            "name": test_project["name"],
            "title": test_project["title"],
            "description": test_project["description"],
            "k8s_cluster_type": "remote",
            "k8s_cluster_kubeconfig": 'apiVersion: v1\nkind: Config\nclusters: []\ncontexts: []\ncurrent-context: ""\nusers: []',
        }
        resp = client.put(
            f"/api/v1/projects/{test_project['id']}",
            json=project_update,
            headers={"X-Project-Id": str(test_project['id'])},
        )
        resp.raise_for_status()

        # 2. Create PgSqlCluster
        model_data = {
            "name": "safety-pg",
            "title": "Safety Postgres",
            "project_id": test_project["id"],
            "instances": 3,
            "storage_size": "2Gi",
        }
        resp = client.post(
            "/api/v1/platform/pgsql",
            json=model_data,
            headers={"X-Project-Id": str(test_project["id"])},
        )
        resp.raise_for_status()
        model_id = resp.json()["data"]["id"]

        # 3. Create state and set to active
        client.post(
            f"/api/v1/platform/pgsql/{model_id}/_state",
            json={"status": "online", "active": True},
            headers={"X-Project-Id": str(test_project["id"])},
        )

        # 4. Decommission without header -> should fail
        resp = client.post(
            f"/api/v1/platform/pgsql/{model_id}/_decommission",
            headers={"X-Project-Id": str(test_project["id"])},
        )
        assert resp.status_code == 422
        assert "X-RESOURCE-NAME header is required" in resp.json()["detail"][0]["msg"]

        # 5. Decommission with wrong header -> should fail
        resp = client.post(
            f"/api/v1/platform/pgsql/{model_id}/_decommission",
            headers={
                "X-Project-Id": str(test_project["id"]),
                "X-RESOURCE-NAME": "wrong-name",
            },
        )
        assert resp.status_code == 422
        assert "does not match resource name" in resp.json()["detail"][0]["msg"]

        # 6. Decommission with correct header -> should succeed
        resp = client.post(
            f"/api/v1/platform/pgsql/{model_id}/_decommission",
            headers={
                "X-Project-Id": str(test_project["id"]),
                "X-RESOURCE-NAME": "safety-pg",
            },
        )
        assert resp.status_code == 200


def test_update_state_active_false_safety_header_required(
    client: TestClient, test_project
):
    with patch(
        "mindweaver.platform_service.base.PlatformService._deploy_to_cluster"
    ), patch(
        "mindweaver.platform_service.base.PlatformService._decommission_from_cluster"
    ), patch(
        "mindweaver.platform_service.pgsql.PgSqlPlatformService.poll_status"
    ):

        # 1. Update project with K8s info
        project_update = {
            "name": test_project["name"],
            "title": test_project["title"],
            "description": test_project["description"],
            "k8s_cluster_type": "remote",
            "k8s_cluster_kubeconfig": 'apiVersion: v1\nkind: Config\nclusters: []\ncontexts: []\ncurrent-context: ""\nusers: []',
        }
        resp = client.put(
            f"/api/v1/projects/{test_project['id']}",
            json=project_update,
            headers={"X-Project-Id": str(test_project['id'])},
        )
        resp.raise_for_status()

        model_data = {
            "name": "safety-pg-2",
            "title": "Safety Postgres 2",
            "project_id": test_project["id"],
            "instances": 3,
            "storage_size": "2Gi",
        }
        resp = client.post(
            "/api/v1/platform/pgsql",
            json=model_data,
            headers={"X-Project-Id": str(test_project["id"])},
        )
        model_id = resp.json()["data"]["id"]

        client.post(
            f"/api/v1/platform/pgsql/{model_id}/_state",
            json={"status": "online", "active": True},
            headers={"X-Project-Id": str(test_project["id"])},
        )

        # 2. Update state active=False without header -> should fail
        resp = client.post(
            f"/api/v1/platform/pgsql/{model_id}/_state",
            json={"active": False},
            headers={"X-Project-Id": str(test_project["id"])},
        )
        assert resp.status_code == 422
        assert "X-RESOURCE-NAME header is required" in resp.json()["detail"][0]["msg"]

        # 3. Update state active=False with correct header -> should succeed
        resp = client.post(
            f"/api/v1/platform/pgsql/{model_id}/_state",
            json={"active": False},
            headers={
                "X-Project-Id": str(test_project["id"]),
                "X-RESOURCE-NAME": "safety-pg-2",
            },
        )
        assert resp.status_code == 200
