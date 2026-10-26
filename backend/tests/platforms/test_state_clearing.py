# SPDX-FileCopyrightText: Copyright © 2026 Mohd Izhar Firdaus Bin Ismail
# SPDX-License-Identifier: AGPLv3+

import pytest
import os
import tempfile
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient
from mindweaver.app import app
from mindweaver.platform_service.base import (
    PlatformBase,
    PlatformService,
    PlatformStateBase,
)
from mindweaver.platform_service.pgsql import (
    PgSqlPlatform,
    PgSqlPlatformState,
    PgSqlPlatformService,
)
from sqlmodel import Session, create_engine
from mindweaver.config import settings


def test_pgsql_platform_service_state_clearing(client: TestClient, test_project):
    """Verifies that platform state is cleared when decommissioned."""
    # 1. Update project with K8s info
    project_update = {
        "name": test_project["name"],
        "title": test_project["title"],
        "description": test_project["description"],
        "k8s_cluster_id": test_project["k8s_cluster_id"],
            "k8s_cluster_type": "remote",
        "k8s_cluster_kubeconfig": 'apiVersion: v1\nkind: Config\nclusters: []\ncontexts: []\ncurrent-context: ""\nusers: []',
    }
    resp = client.put(
        f"/api/v1/projects/{test_project['id']}",
        json=project_update,
        headers={"X-Project-Id": str(test_project['id'])},
    )
    resp.raise_for_status()

    # 2. Setup Model
    model_data = {
        "name": "test-pgsql-clear",
        "title": "Test PgSql Clear",
        "project_id": test_project["id"],
        "instances": 3,
        "storage_size": "1Gi",
    }
    resp = client.post(
        "/api/v1/platform/pgsql",
        json=model_data,
        headers={"X-Project-Id": str(test_project["id"])},
    )
    resp.raise_for_status()
    model_id = resp.json()["data"]["id"]

    # 3. Setup State with some data
    from mindweaver.crypto import encrypt_password

    engine = create_engine(settings.db_uri)
    with Session(engine) as session:
        state = PgSqlPlatformState(
            platform_id=model_id,
            status="online",
            active=True,
            message="Running",
            node_ports=[{"port": 5432, "node_port": 30000}],
            cluster_nodes=[{"hostname": "node1", "ip": "1.2.3.4"}],
            db_user="testuser",
            db_pass=encrypt_password("testpass"),
            db_name="testdb",
            db_ca_crt="testca",
            extra_data={"foo": "bar"},
        )
        session.add(state)
        session.commit()

    # 4. Decommission
    # Mock Kubernetes parts since we don't want actual K8s interaction
    with patch(
        "mindweaver.platform_service.base.PlatformService._decommission_from_cluster",
        return_value=None,
    ):
        with patch(
            "mindweaver.platform_service.base.PlatformService.render_manifests",
            return_value="---",
        ), patch(
            "mindweaver.platform_service.pgsql.PgSqlPlatformService.poll_status",
            return_value=None,
        ):
            resp = client.post(
                f"/api/v1/platform/pgsql/{model_id}/_decommission",
                headers={
                    "X-Project-Id": str(test_project["id"]),
                    "X-RESOURCE-NAME": "test-pgsql-clear",
                },
            )
            resp.raise_for_status()

    # 5. Verify State is cleared
    resp = client.get(
        f"/api/v1/platform/pgsql/{model_id}/_state",
        headers={"X-Project-Id": str(test_project["id"])},
    )
    resp.raise_for_status()
    state_data = resp.json()

    assert state_data["status"] == "offline"
    assert state_data["message"] == "Decommissioned"
    assert state_data["active"] is False
    assert state_data["node_ports"] == []
    assert state_data["cluster_nodes"] == []
    assert state_data["extra_data"] == {}
    assert state_data["db_user"] is None
    assert state_data["db_pass"] is None
    assert state_data["db_name"] is None
    assert state_data["db_ca_crt"] is None


def test_decommission_endpoint_does_not_call_poll_status(client: TestClient, test_project):
    """Verifies that decommission endpoint sets offline state directly and does not call poll_status."""
    model_data = {
        "name": "test-pgsql-nopoll",
        "title": "Test PgSql No Poll",
        "project_id": test_project["id"],
        "instances": 1,
        "storage_size": "1Gi",
    }
    resp = client.post(
        "/api/v1/platform/pgsql",
        json=model_data,
        headers={"X-Project-Id": str(test_project["id"])},
    )
    resp.raise_for_status()
    model_id = resp.json()["data"]["id"]

    engine = create_engine(settings.db_uri)
    with Session(engine) as session:
        state = PgSqlPlatformState(
            platform_id=model_id,
            status="online",
            active=True,
            message="Phase: Cluster in healthy state, Instances: 1/1",
        )
        session.add(state)
        session.commit()

    with patch(
        "mindweaver.platform_service.base.PlatformService._decommission_from_cluster",
        return_value=None,
    ), patch(
        "mindweaver.platform_service.base.PlatformService.render_manifests",
        return_value="---",
    ), patch(
        "mindweaver.platform_service.pgsql.PgSqlPlatformService.poll_status"
    ) as mock_poll:
        resp = client.post(
            f"/api/v1/platform/pgsql/{model_id}/_decommission",
            headers={
                "X-Project-Id": str(test_project["id"]),
                "X-RESOURCE-NAME": "test-pgsql-nopoll",
            },
        )
        resp.raise_for_status()
        mock_poll.assert_not_called()

    resp = client.get(
        f"/api/v1/platform/pgsql/{model_id}/_state",
        headers={"X-Project-Id": str(test_project["id"])},
    )
    resp.raise_for_status()
    state_data = resp.json()
    assert state_data["status"] == "offline"
    assert state_data["message"] == "Decommissioned"
    assert state_data["active"] is False


@pytest.mark.asyncio
async def test_poller_keeps_decommissioned_state_when_inactive(client: TestClient, test_project: dict):
    """Verifies that pollers do not overwrite status to online or healthy if platform is decommissioned/inactive."""
    from mindweaver.platform_service.doris.poller import DorisPoller
    from mindweaver.platform_service.doris.model import DorisPlatform, DorisPlatformState
    from mindweaver.platform_service.doris.service import DorisPlatformService
    from sqlmodel.ext.asyncio.session import AsyncSession
    from mindweaver.fw.model import get_engine

    engine = get_engine()
    async with AsyncSession(engine) as session:
        model = DorisPlatform(
            name="test-doris-inactive",
            title="Test Doris Inactive",
            project_id=test_project["id"],
            fe_replicas=1,
            be_replicas=1,
        )
        session.add(model)
        await session.flush()
        await session.refresh(model)

        state = DorisPlatformState(
            platform_id=model.id,
            status="offline",
            active=False,
            message="Decommissioned",
        )
        session.add(state)
        await session.flush()

        class MockRequest:
            headers = {}

        svc = DorisPlatformService(MockRequest(), session)
        poller = DorisPoller(svc, model)

        # Mock _poll returning online/Healthy (as if K8s resources still exist / terminating)
        with patch.object(
            poller,
            "poll",
            wraps=poller.poll
        ):
            with patch(
                "mindweaver.platform_service.doris.poller.DorisPoller.poll",
            ) as mock_p:
                pass

        # Call poller.poll with an internal _poll returning ('online', 'Sync: Synced, Health: Healthy', {}, [], [])
        with patch(
            "mindweaver.platform_service.doris.poller.asyncio.to_thread",
            return_value=("online", "Sync: Synced, Health: Healthy", {}, [], []),
        ), patch.object(svc, "kubeconfig", return_value=""), patch.object(
            svc, "_resolve_namespace", return_value="default"
        ):
            await poller.poll()

        state = await svc.platform_state(model)
        assert state.status == "offline"
        assert state.message == "Decommissioned"
        assert state.active is False


@pytest.mark.asyncio
async def test_base_state_clear_noop():
    """Verifies that BaseState.clear is a callable async no-op."""
    from mindweaver.fw.state import BaseState

    class DummyState(BaseState):
        async def get(self):
            return {}

    state = DummyState(model=None, svc=None)
    await state.clear()


@pytest.mark.asyncio
async def test_default_platform_state_clear(client: TestClient, test_project: dict):
    """Verifies DefaultPlatformState.clear resets base platform state attributes."""
    from mindweaver.platform_service.base import DefaultPlatformState
    from mindweaver.platform_service.pgsql import PgSqlPlatform, PgSqlPlatformState, PgSqlPlatformService
    from sqlmodel.ext.asyncio.session import AsyncSession
    from mindweaver.fw.model import get_engine

    engine = get_engine()
    async with AsyncSession(engine) as session:
        model = PgSqlPlatform(
            name="test-def-state",
            title="Test Def State",
            project_id=test_project["id"],
            instances=1,
            storage_size="1Gi",
        )
        session.add(model)
        await session.flush()
        await session.refresh(model)

        state = PgSqlPlatformState(
            platform_id=model.id,
            status="online",
            active=True,
            message="Running",
            node_ports=[{"port": 5432}],
            cluster_nodes=[{"hostname": "node1"}],
            extra_data={"key": "val"},
        )
        session.add(state)
        await session.flush()

        class MockRequest:
            headers = {}

        svc = PgSqlPlatformService(MockRequest(), session)
        state_inst = DefaultPlatformState(model, svc)
        await state_inst.clear()

        reloaded = await svc.platform_state(model)
        assert reloaded.status == "offline"
        assert reloaded.message == "Decommissioned"
        assert reloaded.active is False
        assert reloaded.node_ports == []
        assert reloaded.cluster_nodes == []
        assert reloaded.extra_data == {}


@pytest.mark.asyncio
async def test_platform_service_delegates_to_state_class(client: TestClient, test_project: dict):
    """Verifies PlatformService.clear_state delegates to the state object's clear() method."""
    from mindweaver.platform_service.kafka import (
        KafkaPlatform,
        KafkaPlatformState,
        KafkaPlatformService,
    )
    from sqlmodel.ext.asyncio.session import AsyncSession
    from mindweaver.fw.model import get_engine

    engine = get_engine()
    async with AsyncSession(engine) as session:
        model = KafkaPlatform(
            name="test-kafka-clear",
            title="Test Kafka Clear",
            project_id=test_project["id"],
            replica_count=1,
            storage_size="1Gi",
        )
        session.add(model)
        await session.flush()
        await session.refresh(model)

        state = KafkaPlatformState(
            platform_id=model.id,
            status="online",
            active=True,
            message="Ready",
            kafka_url="kafka.default.svc:9092",
            kafka_url_ipv6="[::1]:9092",
        )
        session.add(state)
        await session.flush()

        class MockRequest:
            headers = {}

        svc = KafkaPlatformService(MockRequest(), session)
        await svc.clear_state(model)

        reloaded = await svc.platform_state(model)
        assert reloaded.status == "offline"
        assert reloaded.message == "Decommissioned"
        assert reloaded.active is False
        assert reloaded.kafka_url is None
        assert reloaded.kafka_url_ipv6 is None


@pytest.mark.asyncio
async def test_all_platform_subclass_states_clear(client: TestClient, test_project: dict):
    """Verifies that all 8 platform state subclasses clear their specific attributes."""
    from mindweaver.platform_service.airflow.model import AirflowPlatform, AirflowPlatformState
    from mindweaver.platform_service.airflow.service import AirflowPlatformService
    from mindweaver.platform_service.doris.model import DorisPlatform, DorisPlatformState
    from mindweaver.platform_service.doris.service import DorisPlatformService
    from mindweaver.platform_service.trino.model import TrinoPlatform, TrinoPlatformState
    from mindweaver.platform_service.trino.service import TrinoPlatformService
    from mindweaver.platform_service.superset.model import SupersetPlatform, SupersetPlatformState
    from mindweaver.platform_service.superset.service import SupersetPlatformService
    from mindweaver.platform_service.hive_metastore.model import HiveMetastorePlatform, HiveMetastorePlatformState
    from mindweaver.platform_service.hive_metastore.service import HiveMetastorePlatformService
    from mindweaver.platform_service.nifi.model import NifiPlatform, NifiPlatformState
    from mindweaver.platform_service.nifi.service import NifiPlatformService
    from sqlmodel.ext.asyncio.session import AsyncSession
    from mindweaver.fw.model import get_engine

    engine = get_engine()
    async with AsyncSession(engine) as session:
        class MockRequest:
            headers = {}

        # Create a base pgsql platform for services requiring it
        pg_base = PgSqlPlatform(
            name="test-pg-base",
            title="Test PG Base",
            project_id=test_project["id"],
            instances=1,
            storage_size="1Gi",
        )
        session.add(pg_base)
        await session.flush()
        await session.refresh(pg_base)

        # 1. Airflow
        af_model = AirflowPlatform(
            name="test-af",
            title="Test AF",
            project_id=test_project["id"],
            platform_pgsql_id=pg_base.id,
        )
        session.add(af_model)
        await session.flush()
        af_state = AirflowPlatformState(
            platform_id=af_model.id,
            status="online",
            active=True,
            airflow_uri="http://airflow",
            airflow_uri_ipv6="http://[::1]",
            admin_user="admin",
            admin_password="secret",
        )
        session.add(af_state)
        await session.flush()
        af_svc = AirflowPlatformService(MockRequest(), session)
        await af_svc.clear_state(af_model)
        reloaded = await af_svc.platform_state(af_model)
        assert reloaded.status == "offline"
        assert reloaded.airflow_uri is None
        assert reloaded.airflow_uri_ipv6 is None
        assert reloaded.admin_user is None
        assert reloaded.admin_password is None

        # 2. Doris
        doris_model = DorisPlatform(name="test-doris", title="Test Doris", project_id=test_project["id"], fe_replicas=1, be_replicas=1)
        session.add(doris_model)
        await session.flush()
        doris_state = DorisPlatformState(
            platform_id=doris_model.id,
            status="online",
            active=True,
            query_uri="mysql://doris",
            fe_http_uri="http://doris",
            admin_user="root",
            admin_password="secret",
        )
        session.add(doris_state)
        await session.flush()
        doris_svc = DorisPlatformService(MockRequest(), session)
        await doris_svc.clear_state(doris_model)
        reloaded = await doris_svc.platform_state(doris_model)
        assert reloaded.status == "offline"
        assert reloaded.query_uri is None
        assert reloaded.fe_http_uri is None
        assert reloaded.admin_user is None
        assert reloaded.admin_password is None

        # 3. Trino
        trino_model = TrinoPlatform(name="test-trino", title="Test Trino", project_id=test_project["id"], database_source_ids=[1])
        session.add(trino_model)
        await session.flush()
        trino_state = TrinoPlatformState(
            platform_id=trino_model.id,
            status="online",
            active=True,
            trino_uri="http://trino:8080",
        )
        session.add(trino_state)
        await session.flush()
        trino_svc = TrinoPlatformService(MockRequest(), session)
        await trino_svc.clear_state(trino_model)
        reloaded = await trino_svc.platform_state(trino_model)
        assert reloaded.status == "offline"
        assert reloaded.trino_uri is None

        # 4. Superset
        superset_model = SupersetPlatform(
            name="test-ss",
            title="Test SS",
            project_id=test_project["id"],
            platform_pgsql_id=pg_base.id,
        )
        session.add(superset_model)
        await session.flush()
        superset_state = SupersetPlatformState(
            platform_id=superset_model.id,
            status="online",
            active=True,
            superset_uri="http://superset",
            superset_uri_ipv6="http://[::1]",
            admin_user="admin",
            admin_password="secret",
        )
        session.add(superset_state)
        await session.flush()
        superset_svc = SupersetPlatformService(MockRequest(), session)
        await superset_svc.clear_state(superset_model)
        reloaded = await superset_svc.platform_state(superset_model)
        assert reloaded.status == "offline"
        assert reloaded.superset_uri is None
        assert reloaded.superset_uri_ipv6 is None
        assert reloaded.admin_user is None
        assert reloaded.admin_password is None

        # 5. Hive Metastore
        hms_model = HiveMetastorePlatform(
            name="test-hms",
            title="Test HMS",
            project_id=test_project["id"],
            database_id=pg_base.id,
        )
        session.add(hms_model)
        await session.flush()
        hms_state = HiveMetastorePlatformState(
            platform_id=hms_model.id,
            status="online",
            active=True,
            hms_uri="thrift://hms:9083",
            iceberg_uri="http://hms:8181",
        )
        session.add(hms_state)
        await session.flush()
        hms_svc = HiveMetastorePlatformService(MockRequest(), session)
        await hms_svc.clear_state(hms_model)
        reloaded = await hms_svc.platform_state(hms_model)
        assert reloaded.status == "offline"
        assert reloaded.hms_uri is None
        assert reloaded.iceberg_uri is None

        # 6. NiFi
        nifi_model = NiFiPlatform = NifiPlatform(name="test-nifi", title="Test NiFi", project_id=test_project["id"])
        session.add(nifi_model)
        await session.flush()
        nifi_state = NifiPlatformState(
            platform_id=nifi_model.id,
            status="online",
            active=True,
            nifi_uri="https://nifi:8443",
        )
        session.add(nifi_state)
        await session.flush()
        nifi_svc = NifiPlatformService(MockRequest(), session)
        await nifi_svc.clear_state(nifi_model)
        reloaded = await nifi_svc.platform_state(nifi_model)
        assert reloaded.status == "offline"
        assert reloaded.nifi_uri is None


