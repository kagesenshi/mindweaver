import pytest
from fastapi.testclient import TestClient


def test_create_project(client: TestClient):
    response = client.post(
        "/projects",
        json={
            "name": "test-project",
            "title": "Test Project",
            "description": "A test project",
        },
    )
    assert response.status_code == 200
    data = response.json()["record"]
    assert data["name"] == "test-project"
    assert data["title"] == "Test Project"
    assert data["description"] == "A test project"
    assert "id" in data


def test_list_projects(client: TestClient):
    # Create two projects
    client.post("/projects", json={"name": "p1", "title": "P1"})
    client.post("/projects", json={"name": "p2", "title": "P2"})

    response = client.get("/projects")
    assert response.status_code == 200
    data = response.json()["records"]
    assert len(data) == 2
    names = [p["name"] for p in data]
    assert "p1" in names
    assert "p2" in names


def test_get_project(client: TestClient):
    create_resp = client.post("/projects", json={"name": "p1", "title": "P1"})
    project_id = create_resp.json()["record"]["id"]

    response = client.get(f"/projects/{project_id}")
    assert response.status_code == 200
    data = response.json()["record"]
    assert data["name"] == "p1"


def test_update_project(client: TestClient):
    create_resp = client.post("/projects", json={"name": "p1", "title": "P1"})
    project_id = create_resp.json()["record"]["id"]

    response = client.put(
        f"/projects/{project_id}",
        json={"name": "p1-updated", "title": "P1 Updated"},
    )
    assert response.status_code == 200
    data = response.json()["record"]
    assert data["name"] == "p1"  # Name is immutable
    assert data["title"] == "P1 Updated"


def test_delete_project(client: TestClient):
    create_resp = client.post("/projects", json={"name": "p1", "title": "P1"})
    project_id = create_resp.json()["record"]["id"]

    response = client.delete(f"/projects/{project_id}")
    assert response.status_code == 200

    # Verify it's gone
    get_resp = client.get(f"/projects/{project_id}")
    assert get_resp.status_code == 404


def test_project_scoping(client: TestClient):
    # Create two projects
    p1 = client.post("/projects", json={"name": "p1", "title": "P1"}).json()["record"]
    p2 = client.post("/projects", json={"name": "p2", "title": "P2"}).json()["record"]

    # Create a data source in P1
    headers_p1 = {"X-Project-ID": str(p1["id"])}
    client.post(
        "/data_sources",
        json={
            "project_id": p1["id"],
            "name": "ds1",
            "title": "DS1",
            "type": "API",
            "parameters": {"base_url": "http://example.com", "api_key": "key"},
        },
        headers=headers_p1,
    )

    # Create a data source in P2
    headers_p2 = {"X-Project-ID": str(p2["id"])}
    client.post(
        "/data_sources",
        json={
            "project_id": p2["id"],
            "name": "ds2",
            "title": "DS2",
            "type": "API",
            "parameters": {"base_url": "http://example.com", "api_key": "key"},
        },
        headers=headers_p2,
    )

    # List data sources in P1
    resp_p1 = client.get("/data_sources", headers=headers_p1)
    assert resp_p1.status_code == 200
    recs_p1 = resp_p1.json()["records"]
    assert len(recs_p1) == 1
    assert recs_p1[0]["name"] == "ds1"

    # List data sources in P2
    resp_p2 = client.get("/data_sources", headers=headers_p2)
    assert resp_p2.status_code == 200
    recs_p2 = resp_p2.json()["records"]
    assert len(recs_p2) == 1
    assert recs_p2[0]["name"] == "ds2"

    # List data sources without project header (should show all or none depending on implementation,
    # but based on my implementation of Service.all(), it filters if project_id is passed,
    # if not passed it might return all? Let's check Service.all logic.
    # Actually, in Service.all():
    # stmt = select(cls.model_class())
    # project_id = cls.get_project_id()
    # if project_id:
    #     stmt = stmt.where(cls.model_class().project_id == project_id)
    # So if no header, it returns all.

    resp_all = client.get("/data_sources")
    assert resp_all.status_code == 200
    recs_all = resp_all.json()["records"]
    # Wait, if I didn't add project_id to the model, it won't work.
    # I did add project_id to DataSource model.
    # But wait, did I update the DB schema in the test fixture?
    # The fixture uses SQLModel.metadata.create_all(engine).
    # So it should create the new schema.

    assert len(recs_all) == 2
