from fastapi.testclient import TestClient


def test_name_uniqueness(crud_client: TestClient):
    client = crud_client

    # Create the first record
    resp = client.post(
        "/api/v1/models",
        json={
            "name": "unique-name",
            "title": "First Model",
        },
    )
    resp.raise_for_status()

    # Attempt to create a second record with the same name
    resp = client.post(
        "/api/v1/models",
        json={
            "name": "unique-name",
            "title": "Second Model",
        },
    )

    # Depending on how the exception is handled, it might be 500 (Internal Server Error)
    # or 409 (Conflict) if there is an exception handler for IntegrityError.
    # For now, let's assume it fails.
    assert resp.status_code != 200
    assert resp.status_code != 201
