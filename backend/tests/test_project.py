# SPDX-FileCopyrightText: Copyright © 2025 Mohd Izhar Firdaus Bin Ismail
# SPDX-License-Identifier: AGPLv3+

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch


def test_create_project(client: TestClient):
    response = client.post(
        "/api/v1/projects",
        json={
            "name": "test-project",
            "title": "Test Project",
            "description": "A test project",
        },
    )
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["name"] == "test-project"
    assert data["title"] == "Test Project"
    assert data["description"] == "A test project"
    assert "id" in data


def test_list_projects(client: TestClient):
    # Create two projects
    client.post("/api/v1/projects", json={"name": "p1", "title": "P1"})
    client.post("/api/v1/projects", json={"name": "p2", "title": "P2"})

    response = client.get("/api/v1/projects")
    assert response.status_code == 200
    data = response.json()["data"]
    assert len(data) == 2
    names = [p["name"] for p in data]
    assert "p1" in names
    assert "p2" in names


def test_get_project(client: TestClient):
    create_resp = client.post("/api/v1/projects", json={"name": "p1", "title": "P1"})
    project_id = create_resp.json()["data"]["id"]

    response = client.get(f"/api/v1/projects/{project_id}")
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["name"] == "p1"


def test_update_project(client: TestClient):
    create_resp = client.post("/api/v1/projects", json={"name": "p1", "title": "P1"})
    project_id = create_resp.json()["data"]["id"]

    response = client.put(
        f"/api/v1/projects/{project_id}",
        json={"name": "p1", "title": "P1 Updated"},
    )
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["name"] == "p1"
    assert data["title"] == "P1 Updated"


def test_delete_project(client: TestClient):
    create_resp = client.post("/api/v1/projects", json={"name": "p1", "title": "P1"})
    project_id = create_resp.json()["data"]["id"]

    response = client.delete(
        f"/api/v1/projects/{project_id}", headers={"X-RESOURCE-NAME": "p1"}
    )
    assert response.status_code == 200

    # Verify it's gone
    get_resp = client.get(f"/api/v1/projects/{project_id}")
    assert get_resp.status_code == 404


def test_project_scoping(client: TestClient):
    # Create two projects
    p1 = client.post("/api/v1/projects", json={"name": "p1", "title": "P1"}).json()[
        "data"
    ]
    p2 = client.post("/api/v1/projects", json={"name": "p2", "title": "P2"}).json()[
        "data"
    ]

    # Create a data source in P1
    headers_p1 = {"X-Project-ID": str(p1["id"])}
    resp1 = client.post(
        "/api/v1/data_sources",
        json={
            "project_id": p1["id"],
            "name": "ds1",
            "title": "DS1",
            "driver": "web",
            "parameters": {"base_url": "http://example.com", "api_key": "key"},
        },
        headers=headers_p1,
    )
    assert resp1.status_code == 200, resp1.json()

    # Create a data source in P2
    headers_p2 = {"X-Project-ID": str(p2["id"])}
    resp2 = client.post(
        "/api/v1/data_sources",
        json={
            "project_id": p2["id"],
            "name": "ds2",
            "title": "DS2",
            "driver": "web",
            "parameters": {"base_url": "http://example.com", "api_key": "key"},
        },
        headers=headers_p2,
    )
    assert resp2.status_code == 200, resp2.json()

    # List data sources in P1
    resp_p1 = client.get("/api/v1/data_sources", headers=headers_p1)
    assert resp_p1.status_code == 200
    recs_p1 = resp_p1.json()["data"]
    assert len(recs_p1) == 1
    assert recs_p1[0]["name"] == "ds1"

    # List data sources in P2
    resp_p2 = client.get("/api/v1/data_sources", headers=headers_p2)
    assert resp_p2.status_code == 200
    recs_p2 = resp_p2.json()["data"]
    assert len(recs_p2) == 1
    assert recs_p2[0]["name"] == "ds2"

    resp_all = client.get("/api/v1/data_sources")
    assert resp_all.status_code == 200
    recs_all = resp_all.json()["data"]

    assert len(recs_all) == 2


@patch(
    "mindweaver.platform_service.base.PlatformService._deploy_to_cluster",
    return_value=None,
)
@patch(
    "mindweaver.platform_service.base.PlatformService._decommission_from_cluster",
    return_value=None,
)
@patch(
    "mindweaver.platform_service.pgsql.PgSqlPlatformService.poll_status",
    return_value=None,
)
def test_project_state(
    mock_poll_status, mock_decommission, mock_deploy, client: TestClient
):
    # Create project
    p1 = client.post(
        "/api/v1/projects",
        json={
            "name": "state-test",
            "title": "State Test",
            "k8s_cluster_type": "in-cluster",
        },
    ).json()["data"]

    # Check initial state
    resp = client.get(f"/api/v1/projects/{p1['id']}/_state")
    assert resp.status_code == 200
    state_data = resp.json()
    assert state_data["pgsql"] == 0
    assert state_data["trino"] == 0

    # Create PgSql platform
    headers_p1 = {"X-Project-ID": str(p1["id"])}
    plat = client.post(
        "/api/v1/platform/pgsql",
        json={
            "name": "pg-test",
            "title": "PG Test",
            "instances": 1,
            "project_id": p1["id"],
        },
        headers=headers_p1,
    ).json()["data"]

    # Check state again, should still be 0 since active state hasn't been set
    resp = client.get(f"/api/v1/projects/{p1['id']}/_state")
    assert resp.json()["pgsql"] == 0

    # Update platform state to active
    client.post(
        f"/api/v1/platform/pgsql/{plat['id']}/_state",
        json={"active": True, "status": "online"},
        headers=headers_p1,
    )

    # Check project state, should now be 1
    resp = client.get(f"/api/v1/projects/{p1['id']}/_state")
    assert resp.json()["pgsql"] == 1

    # Decommission platform
    client.post(
        f"/api/v1/platform/pgsql/{plat['id']}/_decommission",
        headers={"X-RESOURCE-NAME": "pg-test", **headers_p1},
    )

    # Check project state, should be 0 again
    resp = client.get(f"/api/v1/projects/{p1['id']}/_state")
    assert resp.json()["pgsql"] == 0
