from fastapi.testclient import TestClient


def test_ai_agent(client: TestClient, test_project):
    resp = client.post(
        "/ai_agents",
        json={
            "project_id": test_project["id"],
            "name": "support-agent",
            "title": "Support Agent",
            "model": "gpt-4",
            "temperature": 0.5,
            "system_prompt": "You are a helpful assistant",
            "status": "Active",
            "knowledge_db_ids": ["db-1", "db-2"],
        },
    )
    resp.raise_for_status()
    data = resp.json()
    assert data["record"]["name"] == "support-agent"
    assert data["record"]["model"] == "gpt-4"

    record_id = data["record"]["id"]
    resp = client.get(f"/ai_agents/{record_id}")
    resp.raise_for_status()
    assert resp.json()["record"]["id"] == record_id
