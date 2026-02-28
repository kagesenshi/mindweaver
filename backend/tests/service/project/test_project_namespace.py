# SPDX-FileCopyrightText: Copyright © 2026 Mohd Izhar Firdaus Bin Ismail
# SPDX-License-Identifier: AGPLv3+

import pytest
from fastapi.testclient import TestClient


def test_create_project_default_namespace(client: TestClient, test_cluster: dict):
    response = client.post(
        "/api/v1/projects",
        json={
            "name": "test-project",
            "title": "Test Project",
            "k8s_cluster_id": test_cluster["id"],
        },
    )
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["name"] == "test-project"
    assert data["k8s_namespace"] == "test-project"


def test_create_project_custom_namespace(client: TestClient, test_cluster: dict):
    response = client.post(
        "/api/v1/projects",
        json={
            "name": "test-project-2",
            "title": "Test Project 2",
            "k8s_namespace": "custom-ns",
            "k8s_cluster_id": test_cluster["id"],
        },
    )
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["name"] == "test-project-2"
    assert data["k8s_namespace"] == "custom-ns"


def test_update_project_namespace_reset(client: TestClient, test_cluster: dict):
    create_resp = client.post(
        "/api/v1/projects",
        json={
            "name": "p-reset",
            "title": "P Reset",
            "k8s_namespace": "initial-ns",
            "k8s_cluster_id": test_cluster["id"],
        },
    )
    assert create_resp.status_code == 200
    project_id = create_resp.json()["data"]["id"]

    # Update to clear k8s_namespace.
    # Put requires all non-nullable fields (name, title, k8s_cluster_id)
    response = client.put(
        f"/api/v1/projects/{project_id}",
        json={
            "name": "p-reset",
            "title": "P Reset",
            "k8s_namespace": "",
            "k8s_cluster_id": test_cluster["id"],
        },
    )
    assert response.status_code == 200
    data = response.json()["data"]
    # Should revert to name because of before_update hook
    assert data["k8s_namespace"] == "p-reset"


def test_platform_resolve_namespace_integration(client: TestClient, test_cluster: dict):
    # Create Project with custom namespace
    proj_resp = client.post(
        "/api/v1/projects",
        json={
            "name": "proj-ns-test",
            "title": "Proj NS Test",
            "k8s_namespace": "target-ns",
            "k8s_cluster_id": test_cluster["id"],
        },
    )
    assert proj_resp.status_code == 200
    project = proj_resp.json()["data"]
    assert project["k8s_namespace"] == "target-ns"

    # Create Project without custom namespace
    proj_resp2 = client.post(
        "/api/v1/projects",
        json={
            "name": "proj-ns-test-2",
            "title": "Proj NS Test 2",
            "k8s_cluster_id": test_cluster["id"],
        },
    )
    assert proj_resp2.status_code == 200
    project2 = proj_resp2.json()["data"]
    assert project2["k8s_namespace"] == "proj-ns-test-2"
