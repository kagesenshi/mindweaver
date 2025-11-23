from fastapi.testclient import TestClient


def test_knowledge_db(client: TestClient, test_project):
    resp = client.post(
        "/knowledge_dbs",
        json={
            "name": "my-docs",
            "title": "My Documentation",
            "type": "vector",
            "description": "A vector database for documentation",
            "parameters": {"embedding_model": "openai", "chunk_size": 1000},
        },
        headers={"X-Project-Id": str(test_project["id"])},
    )
    resp.raise_for_status()
    data = resp.json()
    assert data["record"]["name"] == "my-docs"
    assert data["record"]["type"] == "vector"

    record_id = data["record"]["id"]
    resp = client.get(f"/knowledge_dbs/{record_id}")
    resp.raise_for_status()
    assert resp.json()["record"]["id"] == record_id
