# SPDX-FileCopyrightText: Copyright © 2026 Mohd Izhar Firdaus Bin Ismail
# SPDX-License-Identifier: AGPLv3+

import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from fastapi.testclient import TestClient
from sqlmodel import Session, create_engine, select
from mindweaver.config import settings
from mindweaver.service.k8s_cluster import K8sClusterStatus
from mindweaver.platform_service.pgsql import (
    PgSqlPlatform,
    PgSqlPlatformState,
    PgSqlPlatformService,
)
from mindweaver.platform_service.kafka import (
    KafkaPlatform,
    KafkaPlatformState,
    KafkaPlatformService,
)


def _setup_k8s_and_pgsql(client: TestClient, test_project, pg_name: str) -> tuple[int, int]:
    """Helper to setup project with k8s cluster and create a pgsql platform instance."""
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
        headers={"X-Project-Id": str(test_project["id"])},
    )
    resp.raise_for_status()

    # 2. Create PgSqlCluster
    model_data = {
        "name": pg_name,
        "title": f"Postgres {pg_name}",
        "project_id": test_project["id"],
        "instances": 3,
        "storage_size": "2Gi",
    }
    resp = client.post(
        "/api/v1/platform/pgsql",
        json=model_data,
        headers={"X-Project-Id": str(test_project["id"])},
    )
    resp.raise_for_status()
    model_id = resp.json()["data"]["id"]

    # 3. Mark state as active and online
    engine = create_engine(settings.db_uri)
    with Session(engine) as session:
        state = session.exec(
            select(PgSqlPlatformState).where(PgSqlPlatformState.platform_id == model_id)
        ).first()
        if not state:
            state = PgSqlPlatformState(
                platform_id=model_id,
                status="online",
                active=True,
                message="Running",
            )
            session.add(state)
        else:
            state.active = True
            state.status = "online"
            state.message = "Running"
        session.commit()

    return test_project["k8s_cluster_id"], model_id


def test_decommission_cluster_unreachable_fails_without_force(client: TestClient, test_project):
    """When cluster is unreachable in K8sClusterStatus, decommission must fail with an error."""
    cluster_id, model_id = _setup_k8s_and_pgsql(client, test_project, "unreach-pg-1")

    # Set cluster status to error (unreachable)
    engine = create_engine(settings.db_uri)
    with Session(engine) as session:
        c_status = session.exec(
            select(K8sClusterStatus).where(K8sClusterStatus.k8s_cluster_id == cluster_id)
        ).first()
        if not c_status:
            c_status = K8sClusterStatus(
                k8s_cluster_id=cluster_id,
                status="error",
                message="Cluster is unreachable: Connection timed out",
            )
            session.add(c_status)
        else:
            c_status.status = "error"
            c_status.message = "Cluster is unreachable: Connection timed out"
        session.commit()

    # Attempt decommission via _decommission without force
    resp = client.post(
        f"/api/v1/platform/pgsql/{model_id}/_decommission",
        headers={
            "X-Project-Id": str(test_project["id"]),
            "X-RESOURCE-NAME": "unreach-pg-1",
        },
    )
    assert resp.status_code == 422
    err_detail = resp.json()["detail"]
    assert any("unreachable" in d.get("msg", "").lower() for d in err_detail)

    # Verify cluster state is still active
    resp_state = client.get(
        f"/api/v1/platform/pgsql/{model_id}/_state",
        headers={"X-Project-Id": str(test_project["id"])},
    )
    assert resp_state.status_code == 200
    assert resp_state.json()["active"] is True


def test_decommission_cluster_unreachable_succeeds_with_force_decommission_endpoint(
    client: TestClient, test_project
):
    """When force: 'true' is sent to _decommission, it succeeds even if cluster is unreachable."""
    cluster_id, model_id = _setup_k8s_and_pgsql(client, test_project, "unreach-pg-2")

    engine = create_engine(settings.db_uri)
    with Session(engine) as session:
        c_status = session.exec(
            select(K8sClusterStatus).where(K8sClusterStatus.k8s_cluster_id == cluster_id)
        ).first()
        if not c_status:
            c_status = K8sClusterStatus(
                k8s_cluster_id=cluster_id,
                status="error",
                message="Cluster is unreachable: Connection refused",
            )
            session.add(c_status)
        else:
            c_status.status = "error"
            c_status.message = "Cluster is unreachable: Connection refused"
        session.commit()

    # Call _decommission with force="true" in json payload
    resp = client.post(
        f"/api/v1/platform/pgsql/{model_id}/_decommission",
        json={"force": "true"},
        headers={
            "X-Project-Id": str(test_project["id"]),
            "X-RESOURCE-NAME": "unreach-pg-2",
        },
    )
    assert resp.status_code == 200

    # Verify cluster is now considered decommissioned (offline, active=False)
    resp_state = client.get(
        f"/api/v1/platform/pgsql/{model_id}/_state",
        headers={"X-Project-Id": str(test_project["id"])},
    )
    assert resp_state.status_code == 200
    state_data = resp_state.json()
    assert state_data["active"] is False
    assert state_data["status"] == "offline"


def test_update_state_active_false_unreachable_fails_without_force(client: TestClient, test_project):
    """When cluster is unreachable, setting active: false via _state fails without force."""
    cluster_id, model_id = _setup_k8s_and_pgsql(client, test_project, "unreach-pg-3")

    engine = create_engine(settings.db_uri)
    with Session(engine) as session:
        c_status = session.exec(
            select(K8sClusterStatus).where(K8sClusterStatus.k8s_cluster_id == cluster_id)
        ).first()
        if not c_status:
            c_status = K8sClusterStatus(
                k8s_cluster_id=cluster_id,
                status="error",
                message="Cluster is unreachable: Host unreachable",
            )
            session.add(c_status)
        else:
            c_status.status = "error"
            c_status.message = "Cluster is unreachable: Host unreachable"
        session.commit()

    resp = client.post(
        f"/api/v1/platform/pgsql/{model_id}/_state",
        json={"active": False},
        headers={
            "X-Project-Id": str(test_project["id"]),
            "X-RESOURCE-NAME": "unreach-pg-3",
        },
    )
    assert resp.status_code == 422
    err_detail = resp.json()["detail"]
    assert any("unreachable" in d.get("msg", "").lower() for d in err_detail)


def test_update_state_active_false_unreachable_succeeds_with_force(client: TestClient, test_project):
    """When force: 'true' is sent with active: false via _state, it succeeds and clears state."""
    cluster_id, model_id = _setup_k8s_and_pgsql(client, test_project, "unreach-pg-4")

    engine = create_engine(settings.db_uri)
    with Session(engine) as session:
        c_status = session.exec(
            select(K8sClusterStatus).where(K8sClusterStatus.k8s_cluster_id == cluster_id)
        ).first()
        if not c_status:
            c_status = K8sClusterStatus(
                k8s_cluster_id=cluster_id,
                status="error",
                message="Cluster is unreachable: Host unreachable",
            )
            session.add(c_status)
        else:
            c_status.status = "error"
            c_status.message = "Cluster is unreachable: Host unreachable"
        session.commit()

    resp = client.post(
        f"/api/v1/platform/pgsql/{model_id}/_state",
        json={"active": False, "force": "true"},
        headers={
            "X-Project-Id": str(test_project["id"]),
            "X-RESOURCE-NAME": "unreach-pg-4",
        },
    )
    assert resp.status_code == 200

    resp_state = client.get(
        f"/api/v1/platform/pgsql/{model_id}/_state",
        headers={"X-Project-Id": str(test_project["id"])},
    )
    assert resp_state.status_code == 200
    state_data = resp_state.json()
    assert state_data["active"] is False
    assert state_data["status"] == "offline"


def test_decommission_k8s_exception_fails_without_force_and_succeeds_with_force(
    client: TestClient, test_project
):
    """When _decommission_from_cluster raises an exception (e.g. k8s error):
    Without force -> fails with 422
    With force -> succeeds and considers decommissioned
    """
    _, model_id = _setup_k8s_and_pgsql(client, test_project, "unreach-pg-5")

    with patch.object(
        PgSqlPlatformService,
        "_decommission_from_cluster",
        side_effect=RuntimeError("Connection refused to kubernetes apiserver: 10.0.0.1:6443"),
    ):
        # Without force -> 422
        resp = client.post(
            f"/api/v1/platform/pgsql/{model_id}/_decommission",
            headers={
                "X-Project-Id": str(test_project["id"]),
                "X-RESOURCE-NAME": "unreach-pg-5",
            },
        )
        assert resp.status_code == 422
        err_detail = resp.json()["detail"]
        assert any("unreachable" in d.get("msg", "").lower() or "connection refused" in d.get("msg", "").lower() for d in err_detail)

        # State should still be active
        resp_state = client.get(
            f"/api/v1/platform/pgsql/{model_id}/_state",
            headers={"X-Project-Id": str(test_project["id"])},
        )
        assert resp_state.json()["active"] is True

        # With force: true -> succeeds
        resp = client.post(
            f"/api/v1/platform/pgsql/{model_id}/_decommission",
            json={"force": "true"},
            headers={
                "X-Project-Id": str(test_project["id"]),
                "X-RESOURCE-NAME": "unreach-pg-5",
            },
        )
        assert resp.status_code == 200

        # State should be decommissioned
        resp_state = client.get(
            f"/api/v1/platform/pgsql/{model_id}/_state",
            headers={"X-Project-Id": str(test_project["id"])},
        )
        assert resp_state.json()["active"] is False
        assert resp_state.json()["status"] == "offline"


def _setup_k8s_and_kafka(client: TestClient, test_project, kafka_name: str) -> tuple[int, int]:
    """Helper to setup project with k8s cluster and create a kafka platform instance."""
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
        headers={"X-Project-Id": str(test_project["id"])},
    )
    resp.raise_for_status()

    model_data = {
        "name": kafka_name,
        "title": f"Kafka {kafka_name}",
        "project_id": test_project["id"],
        "replica_count": 3,
        "storage_size": "10Gi",
    }
    resp = client.post(
        "/api/v1/platform/kafka",
        json=model_data,
        headers={"X-Project-Id": str(test_project["id"])},
    )
    resp.raise_for_status()
    model_id = resp.json()["data"]["id"]

    engine = create_engine(settings.db_uri)
    with Session(engine) as session:
        state = session.exec(
            select(KafkaPlatformState).where(KafkaPlatformState.platform_id == model_id)
        ).first()
        if not state:
            state = KafkaPlatformState(
                platform_id=model_id,
                status="online",
                active=True,
                message="Running",
            )
            session.add(state)
        else:
            state.active = True
            state.status = "online"
            state.message = "Running"
        session.commit()

    return test_project["k8s_cluster_id"], model_id


def test_kafka_decommission_unreachable_fails_without_force_and_succeeds_with_force(
    client: TestClient, test_project
):
    """Verifies that Kafka platform service handles unreachable cluster properly."""
    cluster_id, model_id = _setup_k8s_and_kafka(client, test_project, "unreach-kafka-1")

    engine = create_engine(settings.db_uri)
    with Session(engine) as session:
        c_status = session.exec(
            select(K8sClusterStatus).where(K8sClusterStatus.k8s_cluster_id == cluster_id)
        ).first()
        if not c_status:
            c_status = K8sClusterStatus(
                k8s_cluster_id=cluster_id,
                status="error",
                message="Cluster is unreachable: No route to host",
            )
            session.add(c_status)
        else:
            c_status.status = "error"
            c_status.message = "Cluster is unreachable: No route to host"
        session.commit()

    # 1. Without force -> fails with 422
    resp = client.post(
        f"/api/v1/platform/kafka/{model_id}/_decommission",
        headers={
            "X-Project-Id": str(test_project["id"]),
            "X-RESOURCE-NAME": "unreach-kafka-1",
        },
    )
    assert resp.status_code == 422
    assert any("unreachable" in d.get("msg", "").lower() for d in resp.json()["detail"])

    # Verify cluster state is still active
    resp_state = client.get(
        f"/api/v1/platform/kafka/{model_id}/_state",
        headers={"X-Project-Id": str(test_project["id"])},
    )
    assert resp_state.json()["active"] is True

    # 2. With force -> 200 and decommissioned
    resp = client.post(
        f"/api/v1/platform/kafka/{model_id}/_decommission",
        json={"force": "true"},
        headers={
            "X-Project-Id": str(test_project["id"]),
            "X-RESOURCE-NAME": "unreach-kafka-1",
        },
    )
    assert resp.status_code == 200

    resp_state = client.get(
        f"/api/v1/platform/kafka/{model_id}/_state",
        headers={"X-Project-Id": str(test_project["id"])},
    )
    assert resp_state.json()["active"] is False
    assert resp_state.json()["status"] == "offline"
