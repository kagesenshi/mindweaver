# SPDX-FileCopyrightText: Copyright © 2026 Mohd Izhar Firdaus Bin Ismail
# SPDX-License-Identifier: AGPLv3+

import pytest
import uuid
from unittest.mock import patch
from fastapi.testclient import TestClient
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from mindweaver.fw.model import get_engine
from mindweaver.service.dependency_tracker.model import DependencyTracker


@pytest.fixture(autouse=True)
def mock_k8s_cluster_calls():
    """Mock kubernetes client and deployment calls."""
    with patch("mindweaver.platform_service.base.PlatformService._deploy_to_cluster"), \
         patch("mindweaver.platform_service.base.PlatformService._decommission_from_cluster"), \
         patch("mindweaver.platform_service.pgsql.service.PgSqlPlatformService.poll_status"), \
         patch("mindweaver.platform_service.hive_metastore.service.HiveMetastorePlatformService.poll_status"), \
         patch("mindweaver.platform_service.trino.service.TrinoPlatformService.poll_status"):
        yield


def test_dependency_tracker_model_and_aliases():
    """Test DependencyTracker model initialization and property aliases."""
    s_uuid = str(uuid.uuid4())
    d_uuid = str(uuid.uuid4())
    entry = DependencyTracker(
        service_uuid=s_uuid,
        service_name="test-service",
        service_type="hive_metastore",
        dependency_uuid=d_uuid,
        dependency_name="test-dep",
        dependency_type="pgsql",
        relationship="database_id",
    )
    assert entry.service_uuid == s_uuid
    assert entry.source_uuid == s_uuid
    assert entry.service_name == "test-service"
    assert entry.source_name == "test-service"
    assert entry.service_type == "hive_metastore"
    assert entry.source_type == "hive_metastore"

    assert entry.dependency_uuid == d_uuid
    assert entry.target_uuid == d_uuid
    assert entry.dependency_name == "test-dep"
    assert entry.target_name == "test-dep"
    assert entry.dependency_type == "pgsql"
    assert entry.target_type == "pgsql"

    assert entry.relationship == "database_id"
    assert entry.relationship_type == "database_id"

    # Test setter aliases
    entry.target_uuid = "new-d-uuid"
    assert entry.dependency_uuid == "new-d-uuid"
    entry.target_name = "new-dep-name"
    assert entry.dependency_name == "new-dep-name"
    entry.target_type = "new-dep-type"
    assert entry.dependency_type == "new-dep-type"
    entry.source_uuid = "new-s-uuid"
    assert entry.service_uuid == "new-s-uuid"
    entry.source_name = "new-s-name"
    assert entry.service_name == "new-s-name"
    entry.source_type = "new-s-type"
    assert entry.service_type == "new-s-type"
    entry.relationship_type = "new-rel"
    assert entry.relationship == "new-rel"


def test_dependency_tracker_service_crud(client: TestClient):
    """Test CRUD operations on the dependency-tracker API."""
    s_uuid = str(uuid.uuid4())
    d_uuid = str(uuid.uuid4())
    payload = {
        "service_uuid": s_uuid,
        "service_name": "api-service",
        "service_type": "trino",
        "dependency_uuid": d_uuid,
        "dependency_name": "api-dep",
        "dependency_type": "hive_metastore",
        "relationship": "hms_ids",
    }
    # Create
    create_resp = client.post("/api/v1/dependency-tracker", json=payload)
    assert create_resp.status_code == 200, create_resp.text
    created = create_resp.json()["data"]
    item_id = created["id"]
    assert created["service_name"] == "api-service"
    assert created["dependency_name"] == "api-dep"

    # Get by ID
    get_resp = client.get(f"/api/v1/dependency-tracker/{item_id}")
    assert get_resp.status_code == 200
    assert get_resp.json()["data"]["service_uuid"] == s_uuid

    # List
    list_resp = client.get("/api/v1/dependency-tracker")
    assert list_resp.status_code == 200
    items = list_resp.json()["data"]
    assert any(i["id"] == item_id for i in items)

    # Delete
    del_resp = client.delete(
        f"/api/v1/dependency-tracker/{item_id}",
        headers={"X-RESOURCE-NAME": "api-service->api-dep"},
    )
    assert del_resp.status_code == 200


def test_deploy_creates_dependency_and_prevents_decommission(client: TestClient, test_project):
    """
    Test that deploying Hive Metastore creates an entry in DependencyTracker,
    and prevents PostgreSQL dependency from being decommissioned unless HMS is decommissioned or force is used.
    """
    # 1. Create PostgreSQL platform instance
    pgsql_data = {
        "name": "pg-dep-test",
        "title": "PG Dep Test",
        "project_id": test_project["id"],
        "instances": 1,
        "storage_size": "1Gi",
        "cpu_request": 0.5,
        "cpu_limit": 1.0,
        "mem_request": 1.0,
        "mem_limit": 2.0,
    }
    resp = client.post(
        "/api/v1/platform/pgsql",
        json=pgsql_data,
        headers={"X-Project-Id": str(test_project["id"])},
    )
    assert resp.status_code == 200, resp.text
    pg_id = resp.json()["data"]["id"]
    pg_uuid = resp.json()["data"]["uuid"]

    # Deploy PostgreSQL
    deploy_pg = client.post(
        f"/api/v1/platform/pgsql/{pg_id}/_deploy",
        headers={"X-Project-Id": str(test_project["id"])},
    )
    assert deploy_pg.status_code == 200, deploy_pg.text

    # 2. Create Hive Metastore platform instance dependent on PostgreSQL
    hms_data = {
        "name": "hms-dep-test",
        "title": "HMS Dep Test",
        "project_id": test_project["id"],
        "database_id": pg_id,
        "replica_count": 1,
        "cpu_request": 0.5,
        "cpu_limit": 1.0,
        "mem_request": 1.0,
        "mem_limit": 2.0,
    }
    resp_hms = client.post(
        "/api/v1/platform/hive-metastore",
        json=hms_data,
        headers={"X-Project-Id": str(test_project["id"])},
    )
    assert resp_hms.status_code == 200, resp_hms.text
    hms_id = resp_hms.json()["data"]["id"]
    hms_uuid = resp_hms.json()["data"]["uuid"]

    # Deploy Hive Metastore
    deploy_hms = client.post(
        f"/api/v1/platform/hive-metastore/{hms_id}/_deploy",
        headers={"X-Project-Id": str(test_project["id"])},
    )
    assert deploy_hms.status_code == 200, deploy_hms.text

    # 3. Verify DependencyTracker entry was created
    tracker_resp = client.get("/api/v1/dependency-tracker")
    assert tracker_resp.status_code == 200
    entries = tracker_resp.json()["data"]
    match = [
        e for e in entries
        if e["service_uuid"] == hms_uuid and e["dependency_uuid"] == pg_uuid
    ]
    assert len(match) == 1
    dep_entry = match[0]
    assert dep_entry["service_name"] == "hms-dep-test"
    assert dep_entry["service_type"] == "hive_metastore"
    assert dep_entry["dependency_name"] == "pg-dep-test"
    assert dep_entry["dependency_type"] == "pgsql"
    assert dep_entry["relationship"] == "database_id"

    # 4. Attempt to decommission PostgreSQL without force -> should FAIL (422)
    decom_pg = client.post(
        f"/api/v1/platform/pgsql/{pg_id}/_decommission",
        headers={
            "X-Project-Id": str(test_project["id"]),
            "X-RESOURCE-NAME": "pg-dep-test",
        },
    )
    assert decom_pg.status_code == 422, decom_pg.text
    err_msg = decom_pg.text
    assert "hms-dep-test" in err_msg or "hive_metastore" in err_msg

    # 5. Decommission Hive Metastore first -> should SUCCEED
    decom_hms = client.post(
        f"/api/v1/platform/hive-metastore/{hms_id}/_decommission",
        headers={
            "X-Project-Id": str(test_project["id"]),
            "X-RESOURCE-NAME": "hms-dep-test",
        },
    )
    assert decom_hms.status_code == 200, decom_hms.text

    # Verify dependency entry in tracker is now removed
    tracker_resp2 = client.get("/api/v1/dependency-tracker")
    remaining = [
        e for e in tracker_resp2.json()["data"]
        if e["service_uuid"] == hms_uuid
    ]
    assert len(remaining) == 0

    # 6. Now decommission PostgreSQL without force -> should SUCCEED
    decom_pg2 = client.post(
        f"/api/v1/platform/pgsql/{pg_id}/_decommission",
        headers={
            "X-Project-Id": str(test_project["id"]),
            "X-RESOURCE-NAME": "pg-dep-test",
        },
    )
    assert decom_pg2.status_code == 200, decom_pg2.text


def test_force_decommission_fails_when_dependent_is_active(client: TestClient, test_project):
    """Test that decommissioning a dependency with force=True fails if dependent is still deployed/running."""
    # Create and deploy PostgreSQL
    pgsql_data = {
        "name": "pg-force-test",
        "title": "PG Force Test",
        "project_id": test_project["id"],
        "instances": 1,
        "storage_size": "1Gi",
    }
    resp = client.post(
        "/api/v1/platform/pgsql",
        json=pgsql_data,
        headers={"X-Project-Id": str(test_project["id"])},
    )
    pg_id = resp.json()["data"]["id"]

    client.post(
        f"/api/v1/platform/pgsql/{pg_id}/_deploy",
        headers={"X-Project-Id": str(test_project["id"])},
    )

    # Create and deploy HMS
    hms_data = {
        "name": "hms-force-test",
        "title": "HMS Force Test",
        "project_id": test_project["id"],
        "database_id": pg_id,
    }
    resp_hms = client.post(
        "/api/v1/platform/hive-metastore",
        json=hms_data,
        headers={"X-Project-Id": str(test_project["id"])},
    )
    hms_id = resp_hms.json()["data"]["id"]

    client.post(
        f"/api/v1/platform/hive-metastore/{hms_id}/_deploy",
        headers={"X-Project-Id": str(test_project["id"])},
    )

    # Attempt to decommission PostgreSQL with force=True -> MUST FAIL (422)
    decom_force = client.post(
        f"/api/v1/platform/pgsql/{pg_id}/_decommission",
        json={"force": True},
        headers={
            "X-Project-Id": str(test_project["id"]),
            "X-RESOURCE-NAME": "pg-force-test",
        },
    )
    assert decom_force.status_code == 422, decom_force.text
    assert "hms-force-test" in decom_force.text or "hive_metastore" in decom_force.text

    # Decommission HMS first
    decom_hms = client.post(
        f"/api/v1/platform/hive-metastore/{hms_id}/_decommission",
        headers={
            "X-Project-Id": str(test_project["id"]),
            "X-RESOURCE-NAME": "hms-force-test",
        },
    )
    assert decom_hms.status_code == 200, decom_hms.text

    # Now decommission PostgreSQL with force=True -> MUST SUCCEED (200)
    decom_force_ok = client.post(
        f"/api/v1/platform/pgsql/{pg_id}/_decommission",
        json={"force": True},
        headers={
            "X-Project-Id": str(test_project["id"]),
            "X-RESOURCE-NAME": "pg-force-test",
        },
    )
    assert decom_force_ok.status_code == 200, decom_force_ok.text


def test_force_decommission_succeeds_when_dependent_is_not_active(client: TestClient, test_project):
    """Test that decommissioning with force=True succeeds if dependent service in tracker is not active."""
    # Create and deploy PostgreSQL
    pgsql_data = {
        "name": "pg-inactive-dep-test",
        "title": "PG Inactive Dep Test",
        "project_id": test_project["id"],
        "instances": 1,
        "storage_size": "1Gi",
    }
    resp = client.post(
        "/api/v1/platform/pgsql",
        json=pgsql_data,
        headers={"X-Project-Id": str(test_project["id"])},
    )
    pg_id = resp.json()["data"]["id"]
    pg_uuid = resp.json()["data"]["uuid"]

    client.post(
        f"/api/v1/platform/pgsql/{pg_id}/_deploy",
        headers={"X-Project-Id": str(test_project["id"])},
    )

    # Manually add a tracker entry pointing to an inactive/non-existent service
    fake_entry = {
        "service_uuid": "00000000-0000-0000-0000-000000000099",
        "service_name": "ghost-service",
        "service_type": "hive_metastore",
        "dependency_uuid": pg_uuid,
        "dependency_name": "pg-inactive-dep-test",
        "dependency_type": "pgsql",
        "relationship": "database_id",
    }
    tracker_create = client.post(
        "/api/v1/dependency-tracker",
        json=fake_entry,
    )
    assert tracker_create.status_code == 200

    # Decommission PostgreSQL with force=True -> should SUCCEED since ghost service is not active
    decom_force = client.post(
        f"/api/v1/platform/pgsql/{pg_id}/_decommission",
        json={"force": True},
        headers={
            "X-Project-Id": str(test_project["id"]),
            "X-RESOURCE-NAME": "pg-inactive-dep-test",
        },
    )
    assert decom_force.status_code == 200, decom_force.text


def test_multiselect_relationship_dependency_tracking(client: TestClient, test_project):
    """
    Test that a multi-select relationship widget (e.g. Trino's hms_ids)
    creates 1 row in DependencyTracker for each selected dependency.
    """
    # 1. Create PostgreSQL for Hive Metastores
    pg_resp = client.post(
        "/api/v1/platform/pgsql",
        json={"name": "pg-trino-meta", "title": "PG Trino", "project_id": test_project["id"]},
        headers={"X-Project-Id": str(test_project["id"])},
    )
    pg_id = pg_resp.json()["data"]["id"]
    client.post(f"/api/v1/platform/pgsql/{pg_id}/_deploy", headers={"X-Project-Id": str(test_project["id"])})

    # 2. Create two Hive Metastore instances
    hms1_resp = client.post(
        "/api/v1/platform/hive-metastore",
        json={"name": "hms-multi-1", "title": "HMS 1", "project_id": test_project["id"], "database_id": pg_id},
        headers={"X-Project-Id": str(test_project["id"])},
    )
    hms1_id = hms1_resp.json()["data"]["id"]
    hms1_uuid = hms1_resp.json()["data"]["uuid"]
    client.post(f"/api/v1/platform/hive-metastore/{hms1_id}/_deploy", headers={"X-Project-Id": str(test_project["id"])})

    hms2_resp = client.post(
        "/api/v1/platform/hive-metastore",
        json={"name": "hms-multi-2", "title": "HMS 2", "project_id": test_project["id"], "database_id": pg_id},
        headers={"X-Project-Id": str(test_project["id"])},
    )
    hms2_id = hms2_resp.json()["data"]["id"]
    hms2_uuid = hms2_resp.json()["data"]["uuid"]
    client.post(f"/api/v1/platform/hive-metastore/{hms2_id}/_deploy", headers={"X-Project-Id": str(test_project["id"])})

    # 3. Create Trino instance with both Hive Metastores in hms_ids
    trino_data = {
        "name": "trino-multi-test",
        "title": "Trino Multi Test",
        "project_id": test_project["id"],
        "hms_ids": [hms1_id, hms2_id],
    }
    trino_resp = client.post(
        "/api/v1/platform/trino",
        json=trino_data,
        headers={"X-Project-Id": str(test_project["id"])},
    )
    assert trino_resp.status_code == 200, trino_resp.text
    trino_id = trino_resp.json()["data"]["id"]
    trino_uuid = trino_resp.json()["data"]["uuid"]

    # Deploy Trino
    deploy_trino = client.post(
        f"/api/v1/platform/trino/{trino_id}/_deploy",
        headers={"X-Project-Id": str(test_project["id"])},
    )
    assert deploy_trino.status_code == 200, deploy_trino.text

    # 4. Verify 2 rows in DependencyTracker for Trino -> hms1 and Trino -> hms2
    tracker_resp = client.get("/api/v1/dependency-tracker")
    assert tracker_resp.status_code == 200
    entries = tracker_resp.json()["data"]
    trino_entries = [e for e in entries if e["service_uuid"] == trino_uuid]
    assert len(trino_entries) == 2

    dep_uuids = {e["dependency_uuid"] for e in trino_entries}
    assert hms1_uuid in dep_uuids
    assert hms2_uuid in dep_uuids
    for e in trino_entries:
        assert e["service_type"] == "trino"
        assert e["dependency_type"] == "hive_metastore"
        assert e["relationship"] == "hms_ids"

    # 5. Attempt to decommission hms1 -> should fail
    decom_hms1 = client.post(
        f"/api/v1/platform/hive-metastore/{hms1_id}/_decommission",
        headers={"X-Project-Id": str(test_project["id"]), "X-RESOURCE-NAME": "hms-multi-1"},
    )
    assert decom_hms1.status_code == 422
    assert "trino-multi-test" in decom_hms1.text

    # 6. Attempt to decommission hms2 -> should fail
    decom_hms2 = client.post(
        f"/api/v1/platform/hive-metastore/{hms2_id}/_decommission",
        headers={"X-Project-Id": str(test_project["id"]), "X-RESOURCE-NAME": "hms-multi-2"},
    )
    assert decom_hms2.status_code == 422
    assert "trino-multi-test" in decom_hms2.text

    # 7. Decommission Trino -> should succeed and clear tracker rows
    decom_trino = client.post(
        f"/api/v1/platform/trino/{trino_id}/_decommission",
        headers={"X-Project-Id": str(test_project["id"]), "X-RESOURCE-NAME": "trino-multi-test"},
    )
    assert decom_trino.status_code == 200

    # 8. Decommission hms1 and hms2 -> should both succeed now
    assert client.post(
        f"/api/v1/platform/hive-metastore/{hms1_id}/_decommission",
        headers={"X-Project-Id": str(test_project["id"]), "X-RESOURCE-NAME": "hms-multi-1"},
    ).status_code == 200

    assert client.post(
        f"/api/v1/platform/hive-metastore/{hms2_id}/_decommission",
        headers={"X-Project-Id": str(test_project["id"]), "X-RESOURCE-NAME": "hms-multi-2"},
    ).status_code == 200
