from fastapi.testclient import TestClient


def test_chat(client: TestClient, test_project):
    resp = client.post(
        "/api/v1/chats",
        json={
            "name": "chat-session-1",
            "title": "Chat Session 1",
            "agent_id": "agent-123",
            "messages": [
                {"role": "user", "content": "Hello"},
                {"role": "assistant", "content": "Hi there"},
            ],
            "project_id": test_project["id"],
        },
        headers={"X-Project-Id": str(test_project["id"])},
    )
    resp.raise_for_status()
    data = resp.json()
    assert data["record"]["name"] == "chat-session-1"
    assert len(data["record"]["messages"]) == 2

    record_id = data["record"]["id"]
    resp = client.get(f"/api/v1/chats/{record_id}")
    resp.raise_for_status()
    assert resp.json()["record"]["id"] == record_id


def test_list_chats_without_project_id_returns_empty(client: TestClient, test_project):
    # Create a chat in the project
    resp = client.post(
        "/api/v1/chats",
        json={
            "name": "chat-session-1",
            "title": "Chat Session 1",
            "agent_id": "agent-123",
            "messages": [],
            "project_id": test_project["id"],
        },
        headers={"X-Project-Id": str(test_project["id"])},
    )
    resp.raise_for_status()

    # List chats WITHOUT project_id header
    # Should return empty list
    resp = client.get("/api/v1/chats")
    resp.raise_for_status()
    data = resp.json()

    assert len(data["records"]) == 1
    assert data["records"][0]["name"] == "chat-session-1"


def test_delete_chat(client: TestClient, test_project):
    """Test deleting a chat session."""
    # Create a chat session
    create_resp = client.post(
        "/api/v1/chats",
        json={
            "name": "to-delete",
            "title": "To Delete Chat",
            "agent_id": "agent-123",
            "messages": [],
            "project_id": test_project["id"],
        },
        headers={"X-Project-Id": str(test_project["id"])},
    )
    create_resp.raise_for_status()
    chat_id = create_resp.json()["record"]["id"]

    # Delete the chat session
    delete_resp = client.delete(
        f"/api/v1/chats/{chat_id}",
        headers={
            "X-Project-Id": str(test_project["id"]),
            "X-RESOURCE-NAME": "to-delete",
        },
    )
    assert delete_resp.status_code == 200

    # Verify it's gone
    get_resp = client.get(
        f"/api/v1/chats/{chat_id}",
        headers={"X-Project-Id": str(test_project["id"])},
    )
    assert get_resp.status_code == 404
