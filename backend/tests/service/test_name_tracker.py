# SPDX-FileCopyrightText: Copyright © 2026 Mohd Izhar Firdaus Bin Ismail
# SPDX-License-Identifier: AGPLv3+

import pytest
import asyncio
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from mindweaver.fw.model import get_engine, ts_now
from mindweaver.service.name_tracker.model import NameTracker
from mindweaver.platform_service.pgsql.model import PgSqlPlatform
from mindweaver.tasks.name_tracker import scan_and_clean_names


@pytest.fixture
def admin_headers():
    return {}


def test_name_availability_endpoint(client: TestClient, admin_headers):
    # Check initially available name
    response = client.get("/api/v1/name-tracker/_check-availability?name=avail-name", headers=admin_headers)
    assert response.status_code == 200, response.text
    assert response.json()["available"] is True


def test_platform_creation_adds_to_tracker(client: TestClient, test_project, admin_headers):
    # 1. Create a PostgreSQL platform instance
    platform_data = {
        "name": "pg-test-cluster",
        "title": "PG Test Cluster",
        "project_id": test_project["id"],
        "instances": 3,
        "storage_size": "1Gi",
        "image": "ghcr.io/cloudnative-pg/postgresql:18",
        "cpu_request": 0.5,
        "cpu_limit": 1.0,
        "mem_request": 1.0,
        "mem_limit": 2.0,
    }
    
    # Creation
    response = client.post("/api/v1/platform/pgsql", json=platform_data, headers=admin_headers)
    assert response.status_code == 200, response.text
    
    # Verify name availability endpoint now returns False for this name
    avail_response = client.get("/api/v1/name-tracker/_check-availability?name=pg-test-cluster", headers=admin_headers)
    assert avail_response.status_code == 200
    assert avail_response.json()["available"] is False

    # 2. Try to create another PG platform instance with the same name -> should fail
    conflict_data = {
        **platform_data,
        "title": "PG Test Conflict Cluster",
    }
    conflict_response = client.post("/api/v1/platform/pgsql", json=conflict_data, headers=admin_headers)
    assert conflict_response.status_code == 422
    assert "already in use" in conflict_response.text


@pytest.mark.asyncio
async def test_scan_and_clean_names_task(client: TestClient, test_project, admin_headers):
    engine = get_engine()
    
    # 1. Manually insert an expired NameTracker entry (seen 8 days ago)
    async with AsyncSession(engine) as session:
        expired_time = ts_now() - timedelta(days=8)
        expired_entry = NameTracker(
            name="expired-name",
            module="test_module",
            last_seen=expired_time,
        )
        session.add(expired_entry)
        await session.commit()

    # 2. Create a platform instance to ensure we have a valid name in a service table
    platform_data = {
        "name": "scanned-pg-cluster",
        "title": "Scanned PG Cluster",
        "project_id": test_project["id"],
        "instances": 3,
        "storage_size": "1Gi",
        "image": "ghcr.io/cloudnative-pg/postgresql:18",
        "cpu_request": 0.5,
        "cpu_limit": 1.0,
        "mem_request": 1.0,
        "mem_limit": 2.0,
    }
    
    # Avoid hook insertion to test background scanning:
    # Let's delete it from tracker if it was inserted by hook, so scan can recreate/re-discover it.
    response = client.post("/api/v1/platform/pgsql", json=platform_data, headers=admin_headers)
    assert response.status_code == 200, response.text

    async with AsyncSession(engine) as session:
        # Delete from tracker to simulate a name that is in the platform table but missing from tracker
        stmt = select(NameTracker).where(NameTracker.name == "scanned-pg-cluster")
        res = await session.exec(stmt)
        tracker = res.first()
        if tracker:
            await session.delete(tracker)
            await session.commit()

    # 3. Run the scan_and_clean_names function
    await scan_and_clean_names()

    # 4. Verify that:
    # - "scanned-pg-cluster" was restored/scanned in NameTracker
    # - "expired-name" was pruned
    async with AsyncSession(engine) as session:
        stmt_scanned = select(NameTracker).where(NameTracker.name == "scanned-pg-cluster")
        res_scanned = await session.exec(stmt_scanned)
        assert res_scanned.first() is not None

        stmt_expired = select(NameTracker).where(NameTracker.name == "expired-name")
        res_expired = await session.exec(stmt_expired)
        assert res_expired.first() is None


@pytest.mark.asyncio
async def test_platform_service_fails_when_name_exists_in_tracker(client: TestClient, test_project, admin_headers):
    from mindweaver.fw.model import get_engine, ts_now
    from mindweaver.service.name_tracker.model import NameTracker
    from sqlmodel.ext.asyncio.session import AsyncSession

    # Manually populate NameTracker with a name
    engine = get_engine()
    async with AsyncSession(engine) as session:
        tracker = NameTracker(
            name="tracker-exists-name",
            module="manual",
            last_seen=ts_now(),
        )
        session.add(tracker)
        await session.commit()

    # Attempt to create a PostgreSQL platform with the same name
    platform_data = {
        "name": "tracker-exists-name",
        "title": "PG Duplicate Name Cluster",
        "project_id": test_project["id"],
        "instances": 3,
        "storage_size": "1Gi",
        "image": "ghcr.io/cloudnative-pg/postgresql:18",
        "cpu_request": 0.5,
        "cpu_limit": 1.0,
        "mem_request": 1.0,
        "mem_limit": 2.0,
    }
    response = client.post("/api/v1/platform/pgsql", json=platform_data, headers=admin_headers)
    assert response.status_code == 422
    assert "already in use" in response.text

