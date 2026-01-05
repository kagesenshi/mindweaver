from fastapi.testclient import TestClient
from mindweaver.config import logger
import copy


def test_crud(crud_client: TestClient):
    client = crud_client

    resp = client.post(
        "/api/v1/models",
        json={
            "name": "my-model",
            "title": "My Model",
        },
    )

    resp.raise_for_status()
    data = resp.json()
    record_id = data["record"]["id"]

    resp = client.get(f"/api/v1/models/{record_id}")

    resp.raise_for_status()

    result = resp.json()
    assert result["record"]["id"] == record_id
    assert result["record"]["name"] == data["record"]["name"]

    record = data["record"]
    update_request = copy.deepcopy(record)

    update_request["id"] = record_id
    update_request["title"] = "New title"
    update_request["name"] = "new-name"
    resp = client.put(f"/api/v1/models/{record_id}", json=update_request)

    assert resp.status_code == 422
    assert "immutable" in resp.json()["detail"]

    # Now update without changing name
    update_request["name"] = record["name"]
    resp = client.put(f"/api/v1/models/{record_id}", json=update_request)
    resp.raise_for_status()

    updated_record = resp.json()["record"]

    # should remain the same
    assert updated_record["id"] == record["id"]
    assert updated_record["uuid"] == record["uuid"]
    assert updated_record["name"] == record["name"]
    assert updated_record["created"] == record["created"]

    # should change
    assert updated_record["title"] == "New title"
    assert updated_record["modified"] >= record["modified"]

    resp = client.delete(f"/api/v1/models/{record_id}")

    resp.raise_for_status()

    resp = client.get(f"/api/v1/models/{record_id}")

    assert resp.status_code == 404


def test_project_scoped_crud(project_scoped_crud_client: TestClient):
    """Test CRUD operations for ProjectScopedNamedBase models."""
    client = project_scoped_crud_client

    # Create a test project
    resp = client.post(
        "/api/v1/projects",
        json={
            "name": "test-project",
            "title": "Test Project",
            "description": "A test project",
        },
    )
    resp.raise_for_status()
    project_id = resp.json()["record"]["id"]

    # Create a second project for testing project scoping
    resp = client.post(
        "/api/v1/projects",
        json={
            "name": "test-project-2",
            "title": "Test Project 2",
            "description": "Second test project",
        },
    )
    resp.raise_for_status()
    project2_id = resp.json()["record"]["id"]

    resp = client.post(
        "/api/v1/project_scoped_models",
        json={"name": "my-model", "title": "My Model", "project_id": project_id},
        headers={"X-Project-Id": str(project_id)},
    )
    resp.raise_for_status()
    data = resp.json()
    record_id = data["record"]["id"]

    # Verify the record has the correct project_id
    assert data["record"]["project_id"] == project_id

    # Get the record with project_id header
    resp = client.get(
        f"/api/v1/project_scoped_models/{record_id}",
        headers={"X-Project-Id": str(project_id)},
    )
    resp.raise_for_status()
    result = resp.json()
    assert result["record"]["id"] == record_id
    assert result["record"]["name"] == data["record"]["name"]
    assert result["record"]["project_id"] == project_id

    # List all records for project 1 - should return 1 record
    resp = client.get(
        "/api/v1/project_scoped_models", headers={"X-Project-Id": str(project_id)}
    )
    resp.raise_for_status()
    records = resp.json()["records"]
    assert len(records) == 1
    assert records[0]["id"] == record_id

    # List all records for project 2 - should return 0 records
    resp = client.get(
        "/api/v1/project_scoped_models", headers={"X-Project-Id": str(project2_id)}
    )
    resp.raise_for_status()
    records = resp.json()["records"]
    assert len(records) == 0

    # List all records without project_id - should return all records
    resp = client.get("/api/v1/project_scoped_models")
    resp.raise_for_status()
    records = resp.json()["records"]
    assert len(records) == 1

    # Update the record
    record = data["record"]
    update_request = copy.deepcopy(record)
    update_request["id"] = record_id
    update_request["title"] = "New title"
    update_request["name"] = "new-name"
    update_request["project_id"] = project_id

    resp = client.put(
        f"/api/v1/project_scoped_models/{record_id}",
        json=update_request,
        headers={"X-Project-Id": str(project_id)},
    )
    assert resp.status_code == 422
    assert "immutable" in resp.json()["detail"]

    # Now update without changing name
    update_request["name"] = record["name"]
    resp = client.put(
        f"/api/v1/project_scoped_models/{record_id}",
        json=update_request,
        headers={"X-Project-Id": str(project_id)},
    )
    resp.raise_for_status()

    updated_record = resp.json()["record"]

    # Verify immutable fields remain the same
    assert updated_record["id"] == record["id"]
    assert updated_record["uuid"] == record["uuid"]
    assert updated_record["name"] == record["name"]
    assert updated_record["created"] == record["created"]
    assert updated_record["project_id"] == project_id

    # Verify mutable fields changed
    assert updated_record["title"] == "New title"
    assert updated_record["modified"] >= record["modified"]

    # Delete the record
    resp = client.delete(
        f"/api/v1/project_scoped_models/{record_id}",
        headers={"X-Project-Id": str(project_id)},
    )
    resp.raise_for_status()

    # Verify the record is deleted
    resp = client.get(
        f"/api/v1/project_scoped_models/{record_id}",
        headers={"X-Project-Id": str(project_id)},
    )
    assert resp.status_code == 404


def test_project_id_immutability(project_scoped_crud_client: TestClient):
    """Test that project_id is immutable after creation."""
    client = project_scoped_crud_client

    # Create two test projects
    resp = client.post(
        "/api/v1/projects",
        json={"name": "p1", "title": "Project 1"},
    )
    resp.raise_for_status()
    p1_id = resp.json()["record"]["id"]

    resp = client.post(
        "/api/v1/projects",
        json={"name": "p2", "title": "Project 2"},
    )
    resp.raise_for_status()
    p2_id = resp.json()["record"]["id"]

    # Create a record in p1
    resp = client.post(
        "/api/v1/project_scoped_models",
        json={"name": "m1", "title": "Model 1", "project_id": p1_id},
        headers={"X-Project-Id": str(p1_id)},
    )
    resp.raise_for_status()
    record = resp.json()["record"]
    record_id = record["id"]
    assert record["project_id"] == p1_id

    # Attempt to update the record and change project_id to p2_id
    # This should now raise a 422 error
    resp = client.put(
        f"/api/v1/project_scoped_models/{record_id}",
        json={
            "name": record["name"],
            "title": "Updated Title",
            "project_id": p2_id,
        },
        headers={"X-Project-Id": str(p1_id)},
    )
    assert resp.status_code == 422
    assert "immutable" in resp.json()["detail"]

    # Verify that updating without changing project_id still works
    resp = client.put(
        f"/api/v1/project_scoped_models/{record_id}",
        json={
            "name": record["name"],
            "title": "Updated Title",
            "project_id": p1_id,
        },
        headers={"X-Project-Id": str(p1_id)},
    )
    resp.raise_for_status()
    updated_record = resp.json()["record"]

    # Verify project_id remained p1_id
    assert updated_record["project_id"] == p1_id
    assert updated_record["title"] == "Updated Title"

    # Verify that the record is still NOT accessible from p2
    resp = client.get(
        f"/api/v1/project_scoped_models/{record_id}",
        headers={"X-Project-Id": str(p2_id)},
    )
    assert resp.status_code == 404


def test_form_schemas(crud_client: TestClient):
    client = crud_client

    # Test create form
    resp = client.get("/api/v1/models/+create-form")
    resp.raise_for_status()
    data = resp.json()
    schema = data["record"]["jsonschema"]
    assert schema["type"] == "object"
    assert "name" in schema["properties"]

    # Test edit form
    resp = client.get("/api/v1/models/+edit-form")
    resp.raise_for_status()
    data = resp.json()
    schema = data["record"]["jsonschema"]
    assert schema["type"] == "object"
    assert "title" in schema["properties"]
