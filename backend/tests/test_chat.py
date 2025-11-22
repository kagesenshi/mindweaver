from fastapi.testclient import TestClient


def test_chat(client: TestClient, test_project):
    resp = client.post(
        "/chats",
        json={
            "project_id": test_project["id"],
            "name": "chat-session-1",
            "title": "Chat Session 1",
            "agent_id": "agent-123",
            "messages": [
                {"role": "user", "content": "Hello"},
                {"role": "assistant", "content": "Hi there"},
            ],
        },
    )
    resp.raise_for_status()
    data = resp.json()
    assert data["record"]["name"] == "chat-session-1"
    assert len(data["record"]["messages"]) == 2

    record_id = data["record"]["id"]
    resp = client.get(f"/chats/{record_id}")
    resp.raise_for_status()
    assert resp.json()["record"]["id"] == record_id
