from fastapi.testclient import TestClient


def test_knowledge_db(client: TestClient, test_project):
    resp = client.post(
        "/api/v1/knowledge_dbs",
        json={
            "name": "my-docs",
            "title": "My Documentation",
            "type": "knowledge-graph",
            "description": "A knowledge graph for documentation",
            "parameters": {"embedding_model": "openai", "chunk_size": 1000},
        },
        headers={"X-Project-Id": str(test_project["id"])},
    )
    resp.raise_for_status()
    data = resp.json()
    assert data["record"]["name"] == "my-docs"
    assert data["record"]["type"] == "knowledge-graph"

    record_id = data["record"]["id"]
    resp = client.get(f"/api/v1/knowledge_dbs/{record_id}")
    resp.raise_for_status()
    assert resp.json()["record"]["id"] == record_id


def test_list_knowledge_dbs_without_project_id_returns_empty(
    client: TestClient, test_project
):
    """Test that listing knowledge DBs without project_id returns empty list."""
    # Create a knowledge DB in the project
    resp = client.post(
        "/api/v1/knowledge_dbs",
        json={
            "name": "test-kb",
            "title": "Test Knowledge Base",
            "type": "knowledge-graph",
            "description": "Test KB",
            "parameters": {"embedding_model": "openai", "chunk_size": 1000},
        },
        headers={"X-Project-Id": str(test_project["id"])},
    )
    resp.raise_for_status()

    # List knowledge DBs WITHOUT project_id header
    # Should return empty list
    resp = client.get("/api/v1/knowledge_dbs")
    resp.raise_for_status()
    data = resp.json()

    assert len(data["records"]) == 1
    assert data["records"][0]["name"] == "test-kb"


def test_delete_knowledge_db(client: TestClient, test_project):
    """Test deleting a knowledge DB."""
    # Create a knowledge DB
    create_resp = client.post(
        "/api/v1/knowledge_dbs",
        json={
            "name": "to-delete",
            "title": "To Delete KB",
            "type": "knowledge-graph",
            "description": "A knowledge graph to delete",
            "parameters": {"embedding_model": "openai", "chunk_size": 1000},
        },
        headers={"X-Project-Id": str(test_project["id"])},
    )
    create_resp.raise_for_status()
    db_id = create_resp.json()["record"]["id"]

    # Delete the knowledge DB
    delete_resp = client.delete(
        f"/api/v1/knowledge_dbs/{db_id}",
        headers={"X-Project-Id": str(test_project["id"])},
    )
    assert delete_resp.status_code == 200

    # Verify it's gone
    get_resp = client.get(
        f"/api/v1/knowledge_dbs/{db_id}",
        headers={"X-Project-Id": str(test_project["id"])},
    )
    assert get_resp.status_code == 404
