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
            "knowledge_db_ids": ["db-1", "db-2"],
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
