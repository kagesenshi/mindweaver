# SPDX-FileCopyrightText: Copyright © 2026 Mohd Izhar Firdaus Bin Ismail
# SPDX-License-Identifier: AGPLv3+

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch


def test_platform_delete_state_denial_when_active(client: TestClient, test_project):
    with patch(
        "mindweaver.platform_service.base.PlatformService._deploy_to_cluster",
        return_value=None,
    ), patch(
        "mindweaver.platform_service.base.PlatformService._decommission_from_cluster",
        return_value=None,
    ), patch(
        "mindweaver.platform_service.pgsql.PgSqlPlatformService.poll_status",
        return_value=None,
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
            "name": "deny-pg",
            "title": "Deny Postgres",
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

        # 4. Attempt to delete the platform - should fail
        resp = client.delete(
            f"/api/v1/platform/pgsql/{model_id}",
            headers={
                "X-Project-Id": str(test_project["id"]),
                "X-RESOURCE-NAME": "deny-pg",
            },
        )
        assert resp.status_code == 422
        assert (
            "is currently active. Please decommission first"
            in resp.json()["detail"][0]["msg"]
        )


def test_platform_delete_state_success_after_decommission(
    client: TestClient, test_project
):
    with patch(
        "mindweaver.platform_service.base.PlatformService._deploy_to_cluster",
        return_value=None,
    ), patch(
        "mindweaver.platform_service.base.PlatformService._decommission_from_cluster",
        return_value=None,
    ), patch(
        "mindweaver.platform_service.pgsql.PgSqlPlatformService.poll_status",
        return_value=None,
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
            "name": "success-pg",
            "title": "Success Postgres",
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

        # 4. Decommission the platform
        resp = client.post(
            f"/api/v1/platform/pgsql/{model_id}/_decommission",
            headers={
                "X-Project-Id": str(test_project["id"]),
                "X-RESOURCE-NAME": "success-pg",
            },
        )
        resp.raise_for_status()

        # Verify state is NOT active
        resp = client.get(
            f"/api/v1/platform/pgsql/{model_id}/_state",
            headers={"X-Project-Id": str(test_project["id"])},
        )
        assert resp.json().get("active") is False

        # 5. Delete the platform - should succeed now
        resp = client.delete(
            f"/api/v1/platform/pgsql/{model_id}",
            headers={
                "X-Project-Id": str(test_project["id"]),
                "X-RESOURCE-NAME": "success-pg",
            },
        )
        resp.raise_for_status()

        # 6. Verify the state is EXPLICITLY deleted
        resp = client.get(
            f"/api/v1/platform/pgsql/{model_id}/_state",
            headers={"X-Project-Id": str(test_project["id"])},
        )
        assert resp.status_code == 404
