from fastapi.testclient import TestClient


def test_project_form_views(client: TestClient):
    response = client.get("/api/v1/projects/+create-form")
    assert response.status_code == 200
    data = response.json()
    assert "jsonschema" in data["record"]
    assert "widgets" in data["record"]
    assert "immutable_fields" in data["record"]
    assert "internal_fields" in data["record"]

    # Project has no relationships to other registered services in its create form usually
    # But it has immutable fields
    assert "name" in data["record"]["immutable_fields"]
    assert "id" in data["record"]["internal_fields"]


def test_k8s_cluster_form_views(client: TestClient):
    response = client.get("/api/v1/k8s_clusters/+create-form")
    assert response.status_code == 200
    data = response.json()

    # Check enum widget for 'type'
    assert "type" in data["record"]["widgets"]
    assert data["record"]["widgets"]["type"]["type"] == "select"
    assert "options" in data["record"]["widgets"]["type"]
    options = data["record"]["widgets"]["type"]["options"]
    assert any(o["value"] == "remote" and o["label"] == "Remote" for o in options)
    assert any(
        o["value"] == "in-cluster" and o["label"] == "In Cluster" for o in options
    )

    # Check relationship widget for 'project_id'
    assert "project_id" in data["record"]["widgets"]
    assert data["record"]["widgets"]["project_id"]["type"] == "relationship"
    assert data["record"]["widgets"]["project_id"]["endpoint"] == "/api/v1/projects"


def test_ai_agent_form_views(client: TestClient):
    # AIAgent might be under experimental flag, but conftest set them to true
    response = client.get("/api/v1/ai_agents/+create-form")
    if response.status_code == 404:
        import pytest

        pytest.skip("AIAgent service not enabled")

    assert response.status_code == 200
    data = response.json()

    # Check manual widget override for 'knowledge_db_ids'
    assert "knowledge_db_ids" in data["record"]["widgets"]
    assert data["record"]["widgets"]["knowledge_db_ids"]["type"] == "relationship"
    assert data["record"]["widgets"]["knowledge_db_ids"].get("multiselect") is True
    assert (
        data["record"]["widgets"]["knowledge_db_ids"]["endpoint"]
        == "/api/v1/knowledge_dbs"
    )
