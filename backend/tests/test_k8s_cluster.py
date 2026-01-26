from fastapi.testclient import TestClient
import pytest


def test_k8s_cluster_crud(project_scoped_crud_client: TestClient):
    client = project_scoped_crud_client

    # Create a test project
    resp = client.post(
        "/api/v1/projects",
        json={
            "name": "test-project",
            "title": "Test Project",
            "description": "A test project",
        },
    )
    resp.raise_for_status()
    project_id = resp.json()["data"]["id"]

    # 1. Create K8s Cluster
    cluster_data = {
        "name": "test-cluster",
        "title": "Test Cluster",
        "type": "remote",
        "kubeconfig": 'apiVersion: v1\nkind: Config\nclusters: []\ncontexts: []\ncurrent-context: ""\nusers: []',
        "project_id": project_id,
    }
    resp = client.post(
        "/api/v1/k8s_clusters",
        json=cluster_data,
        headers={"X-Project-Id": str(project_id)},
    )
    resp.raise_for_status()
    data = resp.json()
    record_id = data["data"]["id"]
    assert data["data"]["name"] == "test-cluster"
    assert data["data"]["type"] == "remote"
    assert data["data"]["kubeconfig"] == cluster_data["kubeconfig"]

    # 2. Get K8s Cluster
    resp = client.get(
        f"/api/v1/k8s_clusters/{record_id}",
        headers={"X-Project-Id": str(project_id)},
    )
    resp.raise_for_status()
    assert resp.json()["data"]["name"] == "test-cluster"

    # 3. List K8s Clusters
    resp = client.get(
        "/api/v1/k8s_clusters",
        headers={"X-Project-Id": str(project_id)},
    )
    resp.raise_for_status()
    records = resp.json()["data"]
    assert len(records) == 1
    assert records[0]["id"] == record_id

    # 4. Update K8s Cluster
    update_data = {
        "name": "test-cluster",
        "title": "Updated Test Cluster",
        "type": "remote",
        "kubeconfig": cluster_data["kubeconfig"],
        "project_id": project_id,
    }
    resp = client.put(
        f"/api/v1/k8s_clusters/{record_id}",
        json=update_data,
        headers={"X-Project-Id": str(project_id)},
    )
    resp.raise_for_status()
    assert resp.json()["data"]["title"] == "Updated Test Cluster"
    assert resp.json()["data"]["type"] == "remote"

    # 5. Delete K8s Cluster
    resp = client.delete(
        f"/api/v1/k8s_clusters/{record_id}",
        headers={"X-Project-Id": str(project_id), "X-RESOURCE-NAME": "test-cluster"},
    )
    resp.raise_for_status()

    # 6. Verify Deletion
    resp = client.get(
        f"/api/v1/k8s_clusters/{record_id}",
        headers={"X-Project-Id": str(project_id)},
    )
    assert resp.status_code == 404
