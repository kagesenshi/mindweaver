import pytest
from sqlmodel import Session
from fastapi.testclient import TestClient
from mindweaver.service.ontology import Ontology, EntityType, RelationshipType


def test_create_ontology(client: TestClient, test_project):
    response = client.post(
        "/api/v1/ontologies",
        json={
            "name": "test-ontology",
            "title": "Test Ontology",
            "description": "A test ontology",
            "project_id": test_project["id"],
        },
        headers={"X-Project-ID": str(test_project["id"])},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["record"]["name"] == "test-ontology"
    assert data["record"]["title"] == "Test Ontology"
    assert data["record"]["project_id"] == test_project["id"]


def test_list_ontologies(client: TestClient, test_project):
    # Create one first
    client.post(
        "/api/v1/ontologies",
        json={
            "name": "ontology-1",
            "title": "Ontology 1",
            "description": "Desc 1",
            "project_id": test_project["id"],
        },
        headers={"X-Project-ID": str(test_project["id"])},
    )

    response = client.get(
        "/api/v1/ontologies",
        headers={"X-Project-ID": str(test_project["id"])},
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data["records"]) >= 1
    assert any(r["name"] == "ontology-1" for r in data["records"])


def test_update_ontology(client: TestClient, test_project):
    create_res = client.post(
        "/api/v1/ontologies",
        json={
            "name": "to-update",
            "title": "To Update",
            "description": "Old desc",
            "project_id": test_project["id"],
        },
        headers={"X-Project-ID": str(test_project["id"])},
    )
    ontology_id = create_res.json()["record"]["id"]

    # Update allows both description and title
    response = client.put(
        f"/api/v1/ontologies/{ontology_id}",
        json={
            "name": "to-update",
            "description": "New desc",
            "title": "Updated Title",
            "project_id": test_project["id"],
        },
        headers={"X-Project-ID": str(test_project["id"])},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["record"]["description"] == "New desc"
    assert data["record"]["title"] == "Updated Title"


def test_delete_ontology(client: TestClient, test_project):
    create_res = client.post(
        "/api/v1/ontologies",
        json={
            "name": "to-delete",
            "title": "To Delete",
            "description": "Desc",
            "project_id": test_project["id"],
        },
        headers={"X-Project-ID": str(test_project["id"])},
    )
    ontology_id = create_res.json()["record"]["id"]

    response = client.delete(
        f"/api/v1/ontologies/{ontology_id}",
        headers={"X-Project-ID": str(test_project["id"])},
    )
    assert response.status_code == 200

    # Verify it's gone
    get_res = client.get(
        f"/api/v1/ontologies/{ontology_id}",
        headers={"X-Project-ID": str(test_project["id"])},
    )
    assert get_res.status_code == 404
