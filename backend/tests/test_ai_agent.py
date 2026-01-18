from fastapi.testclient import TestClient


def test_ai_agent(client: TestClient, test_project):
    resp = client.post(
        "/api/v1/ai_agents",
        json={
            "name": "support-agent",
            "title": "Support Agent",
            "model": "gpt-4",
            "temperature": 0.5,
            "system_prompt": "You are a helpful assistant",
            "status": "Active",
            "knowledge_db_ids": [1, 2],
            "project_id": test_project["id"],
        },
        headers={"X-Project-Id": str(test_project["id"])},
    )
    resp.raise_for_status()
    data = resp.json()
    assert data["record"]["name"] == "support-agent"
    assert data["record"]["model"] == "gpt-4"

    record_id = data["record"]["id"]
    resp = client.get(f"/api/v1/ai_agents/{record_id}")
    resp.raise_for_status()
    assert resp.json()["record"]["id"] == record_id


def test_list_ai_agents_without_project_id_returns_empty(
    client: TestClient, test_project
):
    """Test that listing AI agents without project_id returns empty list."""
    # Create an AI agent in the project
    resp = client.post(
        "/api/v1/ai_agents",
        json={
            "name": "test-agent",
            "title": "Test Agent",
            "model": "gpt-4",
            "temperature": 0.7,
            "system_prompt": "You are a helpful assistant",
            "status": "Active",
            "knowledge_db_ids": [],
            "project_id": test_project["id"],
        },
        headers={"X-Project-Id": str(test_project["id"])},
    )
    resp.raise_for_status()

    # List AI agents WITHOUT project_id header
    # Should return empty list
    resp = client.get("/api/v1/ai_agents")
    resp.raise_for_status()
    data = resp.json()

    assert len(data["records"]) == 1
    assert data["records"][0]["name"] == "test-agent"


def test_delete_ai_agent(client: TestClient, test_project):
    """Test deleting an AI agent."""
    # Create an AI agent
    create_resp = client.post(
        "/api/v1/ai_agents",
        json={
            "name": "to-delete",
            "title": "To Delete Agent",
            "model": "gpt-4",
            "temperature": 0.5,
            "system_prompt": "You are a helpful assistant",
            "status": "Active",
            "knowledge_db_ids": [],
            "project_id": test_project["id"],
        },
        headers={"X-Project-Id": str(test_project["id"])},
    )
    create_resp.raise_for_status()
    agent_id = create_resp.json()["record"]["id"]

    # Delete the AI agent
    delete_resp = client.delete(
        f"/api/v1/ai_agents/{agent_id}",
        headers={
            "X-Project-Id": str(test_project["id"]),
            "X-RESOURCE-NAME": "to-delete",
        },
    )
    assert delete_resp.status_code == 200

    # Verify it's gone
    get_resp = client.get(
        f"/api/v1/ai_agents/{agent_id}",
        headers={"X-Project-Id": str(test_project["id"])},
    )
    assert get_resp.status_code == 404
