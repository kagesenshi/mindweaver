from fastapi.testclient import TestClient


def test_chat(client: TestClient, test_project):
    resp = client.post(
        "/chats",
        json={
            "name": "chat-session-1",
            "title": "Chat Session 1",
            "agent_id": "agent-123",
            "messages": [
                {"role": "user", "content": "Hello"},
                {"role": "assistant", "content": "Hi there"},
            ],
        },
        headers={"X-Project-Id": str(test_project["id"])},
    )
    resp.raise_for_status()
    data = resp.json()
    assert data["record"]["name"] == "chat-session-1"
    assert len(data["record"]["messages"]) == 2

    record_id = data["record"]["id"]
    resp = client.get(f"/chats/{record_id}")
    resp.raise_for_status()
    assert resp.json()["record"]["id"] == record_id


def test_list_chats_without_project_id_returns_empty(client: TestClient, test_project):
    # Create a chat in the project
    resp = client.post(
        "/chats",
        json={
            "name": "chat-session-1",
            "title": "Chat Session 1",
            "agent_id": "agent-123",
            "messages": [],
        },
        headers={"X-Project-Id": str(test_project["id"])},
    )
    resp.raise_for_status()

    # List chats WITHOUT project_id header
    # Should return empty list
    resp = client.get("/chats")
    resp.raise_for_status()
    data = resp.json()

    assert data["records"] == []
