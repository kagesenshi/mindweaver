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
    # 1. Setup K8sCluster
    cluster_data = {
        "name": "test-cluster-clear",
        "title": "Test Cluster Clear",
        "type": "remote",
        "kubeconfig": 'apiVersion: v1\nkind: Config\nclusters: []\ncontexts: []\ncurrent-context: ""\nusers: []',
        "project_id": test_project["id"],
    }
    resp = client.post(
        "/api/v1/k8s_clusters",
        json=cluster_data,
        headers={"X-Project-Id": str(test_project["id"])},
    )
    resp.raise_for_status()
    cluster_id = resp.json()["record"]["id"]

    # 2. Setup Model
    model_data = {
        "name": "test-pgsql-clear",
        "title": "Test PgSql Clear",
        "project_id": test_project["id"],
        "k8s_cluster_id": cluster_id,
        "instances": 3,
        "storage_size": "1Gi",
    }
    resp = client.post(
        "/api/v1/platform/pgsql",
        json=model_data,
        headers={"X-Project-Id": str(test_project["id"])},
    )
    resp.raise_for_status()
    model_id = resp.json()["record"]["id"]

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
                headers={"X-Project-Id": str(test_project["id"])},
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
