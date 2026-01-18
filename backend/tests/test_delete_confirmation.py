from fastapi.testclient import TestClient
from mindweaver.config import logger


def test_delete_confirmation_header(crud_client: TestClient):
    client = crud_client

    # 1. Create a model
    resp = client.post(
        "/api/v1/models",
        json={
            "name": "test-model",
            "title": "Test Model",
        },
    )
    resp.raise_for_status()
    record_id = resp.json()["record"]["id"]

    # 2. Try to delete without header - should fail
    resp = client.delete(f"/api/v1/models/{record_id}")
    assert resp.status_code == 422
    assert "X-RESOURCE-NAME" in resp.json()["detail"][0]["msg"]

    # 3. Try to delete with wrong header - should fail
    resp = client.delete(
        f"/api/v1/models/{record_id}", headers={"X-RESOURCE-NAME": "wrong-name"}
    )
    assert resp.status_code == 422
    assert "must match the resource name" in resp.json()["detail"][0]["msg"]

    # 4. Delete with correct header - should succeed
    resp = client.delete(
        f"/api/v1/models/{record_id}", headers={"X-RESOURCE-NAME": "test-model"}
    )
    resp.raise_for_status()

    # 5. Verify it's deleted
    resp = client.get(f"/api/v1/models/{record_id}")
    assert resp.status_code == 404
