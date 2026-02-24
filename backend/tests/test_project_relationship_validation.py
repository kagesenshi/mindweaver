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

    # 2. Create a DataSource in Project Alpha
    headers_p1 = {"X-Project-ID": str(p1["id"])}
    resp_ds1 = client.post(
        "/api/v1/data_sources",
        json={
            "project_id": p1["id"],
            "name": "ds-alpha",
            "title": "Alpha DataSource",
            "driver": "web",
            "parameters": {"base_url": "http://alpha.com", "api_key": "key"},
        },
        headers=headers_p1,
    )
    assert resp_ds1.status_code == 200, resp_ds1.json()
    ds1 = resp_ds1.json()["data"]

    # 3. Create an S3 Storage in Project Beta
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

    # 4. Attempt to create an Ingestion in Project Beta referencing Alpha DataSource
    resp = client.post(
        "/api/v1/ingestions",
        json={
            "project_id": p2["id"],
            "name": "ing-cross",
            "title": "Cross Ingestion",
            "data_source_id": ds1["id"],
            "s3_storage_id": s3_beta["id"],
            "storage_path": "test/",
            "cron_schedule": "0 0 * * *",
            "ingestion_type": "full_refresh",
            "config": {},
        },
        headers=headers_p2,
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

    # 2. Create DataSource and S3 in Gamma
    resp_ds1 = client.post(
        "/api/v1/data_sources",
        json={
            "project_id": p1["id"],
            "name": "ds-gamma",
            "title": "Gamma DataSource",
            "driver": "web",
            "parameters": {"base_url": "http://gamma.com", "api_key": "key"},
        },
        headers=headers_p1,
    )
    assert resp_ds1.status_code == 200, resp_ds1.json()
    ds1 = resp_ds1.json()["data"]

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

    # 3. Create Ingestion in Gamma - should work
    resp = client.post(
        "/api/v1/ingestions",
        json={
            "project_id": p1["id"],
            "name": "ing-gamma",
            "title": "Gamma Ingestion",
            "data_source_id": ds1["id"],
            "s3_storage_id": s3_gamma["id"],
            "storage_path": "test/",
            "cron_schedule": "0 0 * * *",
            "ingestion_type": "full_refresh",
            "config": {},
        },
        headers=headers_p1,
    )
    assert resp.status_code == 200, resp.json()
