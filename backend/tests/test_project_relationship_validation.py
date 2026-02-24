# SPDX-FileCopyrightText: Copyright © 2026 Mohd Izhar Firdaus Bin Ismail
# SPDX-License-Identifier: AGPLv3+

import pytest
from fastapi.testclient import TestClient


def test_cross_project_relationship_validation(client: TestClient):
    # 1. Create two projects
    resp_p1 = client.post(
        "/api/v1/projects", json={"name": "p-alpha", "title": "Project Alpha"}
    )
    assert resp_p1.status_code == 200, resp_p1.json()
    p1 = resp_p1.json()["data"]

    resp_p2 = client.post(
        "/api/v1/projects", json={"name": "p-beta", "title": "Project Beta"}
    )
    assert resp_p2.status_code == 200, resp_p2.json()
    p2 = resp_p2.json()["data"]

    # 2. Create an S3 Storage in Project Beta
    headers_p2 = {"X-Project-ID": str(p2["id"])}
    resp_s3 = client.post(
        "/api/v1/s3_storages",
        json={
            "project_id": p2["id"],
            "name": "s3-beta",
            "title": "Beta S3",
            "region": "us-east-1",
            "access_key": "somekey",
            "secret_key": "somesecret",
        },
        headers=headers_p2,
    )
    assert resp_s3.status_code == 200, resp_s3.json()
    s3_beta = resp_s3.json()["data"]

    # 3. Attempt to create a PgSQL Platform in Project Alpha referencing Beta S3 Storage
    headers_p1 = {"X-Project-ID": str(p1["id"])}
    resp = client.post(
        "/api/v1/platform/pgsql",
        json={
            "project_id": p1["id"],
            "name": "pgsql-cross",
            "title": "Cross PgSQL",
            "version": "14",
            "storage_class": "standard",
            "storage_size": "10Gi",
            "s3_backup": True,
            "s3_storage_id": s3_beta["id"],
        },
        headers=headers_p1,
    )

    # We WANT it to fail with 422
    assert (
        resp.status_code == 422
    ), f"Expected 422 but got {resp.status_code}: {resp.text}"
    assert "project" in str(resp.json()["detail"]).lower()


def test_same_project_relationship_works(client: TestClient):
    # 1. Create a project
    resp_p1 = client.post(
        "/api/v1/projects", json={"name": "p-gamma", "title": "Project Gamma"}
    )
    assert resp_p1.status_code == 200, resp_p1.json()
    p1 = resp_p1.json()["data"]
    headers_p1 = {"X-Project-ID": str(p1["id"])}

    # 2. Create S3 in Gamma
    resp_s3 = client.post(
        "/api/v1/s3_storages",
        json={
            "project_id": p1["id"],
            "name": "s3-gamma",
            "title": "Gamma S3",
            "region": "us-east-1",
            "access_key": "somekey",
            "secret_key": "somesecret",
        },
        headers=headers_p1,
    )
    assert resp_s3.status_code == 200, resp_s3.json()
    s3_gamma = resp_s3.json()["data"]

    # 3. Create PgSQL Platform in Gamma - should work
    resp = client.post(
        "/api/v1/platform/pgsql",
        json={
            "project_id": p1["id"],
            "name": "pgsql-gamma",
            "title": "Gamma PgSQL",
            "version": "14",
            "storage_class": "standard",
            "storage_size": "10Gi",
            "s3_backup": True,
            "s3_storage_id": s3_gamma["id"],
        },
        headers=headers_p1,
    )
    assert resp.status_code == 200, resp.json()
