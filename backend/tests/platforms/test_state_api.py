import pytest
from fastapi.testclient import TestClient
from datetime import datetime


def test_platform_state_api(client: TestClient, test_project):
    # 1. Setup K8sCluster
    cluster_data = {
        "name": "test-cluster-state",
        "title": "Test Cluster State",
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
        "name": "state-pg",
        "title": "State Postgres",
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

    # 3. Get initial state (should be empty object or default)
    resp = client.get(
        f"/api/v1/platform/pgsql/{model_id}/+state",
        headers={"X-Project-Id": str(test_project["id"])},
    )
    resp.raise_for_status()
    # If no state created yet, it returns {} as per implementation
    assert resp.json() == {}

    # 4. Update state
    update_data = {
        "status": "online",
        "active": True,
        "message": "Cluster is running",
        "extra_data": {"nodes": 3},
    }
    resp = client.post(
        f"/api/v1/platform/pgsql/{model_id}/+state",
        json=update_data,
        headers={"X-Project-Id": str(test_project["id"])},
    )
    resp.raise_for_status()
    state = resp.json()
    assert state["status"] == "online"
    assert state["active"] is True
    assert state["message"] == "Cluster is running"
    assert state["extra_data"] == {"nodes": 3}
    assert "last_heartbeat" in state
    assert state["last_heartbeat"] is not None

    # 5. Get state again
    resp = client.get(
        f"/api/v1/platform/pgsql/{model_id}/+state",
        headers={"X-Project-Id": str(test_project["id"])},
    )
    resp.raise_for_status()
    state = resp.json()
    assert state["status"] == "online"
    assert state["platform_id"] == model_id

    # 6. Partial update
    partial_update = {"status": "error", "message": "Something went wrong"}
    resp = client.post(
        f"/api/v1/platform/pgsql/{model_id}/+state",
        json=partial_update,
        headers={"X-Project-Id": str(test_project["id"])},
    )
    resp.raise_for_status()
    state = resp.json()
    assert state["status"] == "error"
    assert state["active"] is True  # Should remain unchanged
    assert state["message"] == "Something went wrong"
    assert state["extra_data"] == {"nodes": 3}  # Should remain unchanged
