# SPDX-FileCopyrightText: Copyright © 2026 Mohd Izhar Firdaus Bin Ismail
# SPDX-License-Identifier: AGPLv3+

from fastapi.testclient import TestClient


def test_project_form_views(client: TestClient):
    response = client.get("/api/v1/projects/_create-form")
    assert response.status_code == 200
    data = response.json()
    assert "jsonschema" in data["data"]
    assert "widgets" in data["data"]
    assert "immutable_fields" in data["data"]
    assert "internal_fields" in data["data"]

    # Project has no relationships to other registered services in its create form usually
    # But it has immutable fields
    assert "name" in data["data"]["immutable_fields"]
    assert "id" in data["data"]["internal_fields"]

    # Check K8s fields in project form
    assert "k8s_cluster_type" in data["data"]["widgets"]
    assert data["data"]["widgets"]["k8s_cluster_type"]["type"] == "select"
    assert "k8s_cluster_kubeconfig" in data["data"]["widgets"]
    assert data["data"]["widgets"]["k8s_cluster_kubeconfig"]["type"] == "textarea"
