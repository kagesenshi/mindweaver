# SPDX-FileCopyrightText: Copyright © 2026 Mohd Izhar Firdaus Bin Ismail
# SPDX-License-Identifier: AGPLv3+

import pytest
from unittest.mock import MagicMock, patch, call
from fastapi.testclient import TestClient
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy.ext.asyncio import create_async_engine
from mindweaver.service.k8s_cluster.model import (
    K8sClusterStatus,
    K8sClusterType,
    K8sCluster,
)
from mindweaver.config import settings


@pytest.fixture
def mock_k8s():
    with patch(
        "mindweaver.service.k8s_cluster.service.config.load_incluster_config"
    ), patch(
        "mindweaver.service.k8s_cluster.service.client.CoreV1Api"
    ) as mock_core, patch(
        "mindweaver.service.k8s_cluster.service.client.VersionApi"
    ) as mock_version:

        # Mock Version
        mock_v = MagicMock()
        mock_v.git_version = "v1.27.0"
        mock_version.return_value.get_code.return_value = mock_v

        # Mock Nodes
        mock_node = MagicMock()
        mock_node.metadata.name = "node-1"
        mock_node.status.conditions = [MagicMock(type="Ready", status="True")]
        mock_node.status.capacity = {"cpu": "2", "memory": "4Gi"}

        mock_nodes_list = MagicMock()
        mock_nodes_list.items = [mock_node]
        mock_core.return_value.list_node.return_value = mock_nodes_list

        # Mock Services (ArgoCD)
        mock_svc = MagicMock()
        mock_svc.metadata.name = "argocd-server"
        mock_svc_list = MagicMock()
        mock_svc_list.items = [mock_svc]
        mock_core.return_value.list_service_for_all_namespaces.return_value = (
            mock_svc_list
        )

        # Mock Pods (ArgoCD version)
        mock_pod_argo = MagicMock()
        mock_pod_argo.metadata.labels = {"app.kubernetes.io/version": "v2.8.0"}
        mock_pod_argo.spec.containers = [MagicMock(image="argoproj/argocd:v2.8.0")]

        # Mock Pods (Cert Manager version)
        mock_pod_cm = MagicMock()
        mock_pod_cm.metadata.labels = {"app.kubernetes.io/version": "v1.20.0"}
        mock_pod_cm.spec.containers = [MagicMock(image="cert-manager:v1.20.0")]

        # Mock Pods (CNPG version - NO LABEL FALLBACK)
        mock_pod_cnpg = MagicMock()
        mock_pod_cnpg.metadata.labels = {}
        mock_pod_cnpg.spec.containers = [
            MagicMock(image="ghcr.io/cloudnative-pg/cloudnative-pg:1.28.1")
        ]

        def _mock_list_pod_for_all_namespaces(label_selector=None):
            m_list = MagicMock()
            if "argocd-server" in label_selector:
                m_list.items = [mock_pod_argo]
            elif "cert-manager" in label_selector:
                m_list.items = [mock_pod_cm]
            elif "cloudnative-pg" in label_selector:
                m_list.items = [mock_pod_cnpg]
            else:
                m_list.items = []
            return m_list

        mock_core.return_value.list_pod_for_all_namespaces.side_effect = (
            _mock_list_pod_for_all_namespaces
        )

        # Mock Secrets (Helm Release)
        mock_secret_argo = MagicMock()
        mock_secret_argo.metadata.name = "sh.helm.release.v1.argocd.v1"
        mock_secret_cm = MagicMock()
        mock_secret_cm.metadata.name = "sh.helm.release.v1.cert-manager.v1"
        mock_secret_cnpg = MagicMock()
        mock_secret_cnpg.metadata.name = "sh.helm.release.v1.cnpg.v1"

        mock_secret_list = MagicMock()
        mock_secret_list.items = [mock_secret_argo, mock_secret_cm, mock_secret_cnpg]
        mock_core.return_value.list_secret_for_all_namespaces.return_value = (
            mock_secret_list
        )

        yield {"core": mock_core, "version": mock_version}


def test_poll_k8s_cluster_status(client: TestClient, mock_k8s):
    # Create cluster
    p1 = client.post(
        "/api/v1/k8s_clusters",
        json={
            "name": "poll-test",
            "title": "Poll Test",
            "type": "in-cluster",
        },
    ).json()["data"]

    # Trigger refresh
    resp = client.post(f"/api/v1/k8s_clusters/{p1['id']}/_refresh")
    assert resp.status_code == 200

    # Check state
    resp_state = client.get(f"/api/v1/k8s_clusters/{p1['id']}/_state")
    assert resp_state.status_code == 200
    data = resp_state.json()

    assert data["status"] == "online"
    assert data["k8s_version"] == "v1.27.0"
    assert data["node_count"] == 1
    assert data["cpu_total"] == 2.0
    assert data["ram_total"] == 4.0
    assert data["argocd_installed"] is True
    assert data["argocd_version"] == "v2.8.0"
    assert data["cert_manager_installed"] is True
    assert data["cert_manager_version"] == "v1.20.0"
    assert data["cnpg_installed"] is True
    assert data["cnpg_version"] == "1.28.1"


@pytest.mark.asyncio
async def test_install_argocd():
    from mindweaver.service.k8s_cluster.service import K8sClusterService

    cluster = K8sCluster(
        name="test-cluster-argo",
        title="Test Cluster Argo",
        type=K8sClusterType.REMOTE,
        kubeconfig="fake-kubeconfig",
    )

    mock_svc = MagicMock()
    mock_svc.kubeconfig = pytest.importorskip("unittest.mock").AsyncMock(
        return_value="fake-kubeconfig"
    )

    from mindweaver.service.k8s_cluster.actions import InstallArgoCDAction

    with patch("asyncio.create_subprocess_exec") as mock_exec:
        mock_proc = MagicMock()
        mock_proc.returncode = 0
        mock_proc.communicate = pytest.importorskip("unittest.mock").AsyncMock(
            return_value=(b"success", b"")
        )
        mock_exec.return_value = mock_proc

        action = InstallArgoCDAction(cluster, mock_svc)
        await action.run()

        # Verify helm repo add
        # Verify helm upgrade --install
        assert mock_exec.call_count >= 3  # add, update, upgrade

        calls = [call[0] for call in mock_exec.call_args_list]
        found_upgrade = False
        for call_args in calls:
            if "upgrade" in call_args and "--install" in call_args:
                found_upgrade = True
                assert "argo/argo-cd" in call_args
                assert "--kubeconfig" in call_args

        assert found_upgrade


@pytest.mark.asyncio
async def test_install_cert_manager():
    from mindweaver.service.k8s_cluster.model import K8sCluster, K8sClusterType

    cluster = K8sCluster(
        name="test-cluster-cm",
        title="Test Cluster CM",
        type=K8sClusterType.REMOTE,
        kubeconfig="fake-kubeconfig",
    )

    mock_svc = MagicMock()
    mock_svc.kubeconfig = pytest.importorskip("unittest.mock").AsyncMock(
        return_value="fake-kubeconfig"
    )

    from mindweaver.service.k8s_cluster.actions import InstallCertManagerAction

    with patch("asyncio.create_subprocess_exec") as mock_exec:
        mock_proc = MagicMock()
        mock_proc.returncode = 0
        mock_proc.communicate = pytest.importorskip("unittest.mock").AsyncMock(
            return_value=(b"success", b"")
        )
        mock_exec.return_value = mock_proc

        action = InstallCertManagerAction(cluster, mock_svc)
        await action.run()

        # Verify helm repo add
        # Verify helm upgrade --install
        assert mock_exec.call_count >= 3  # add, update, upgrade

        calls = [call[0] for call in mock_exec.call_args_list]
        found_upgrade = False
        for call_args in calls:
            if "upgrade" in call_args and "--install" in call_args:
                if "cert-manager" in call_args:
                    found_upgrade = True
                    assert "jetstack/cert-manager" in call_args
                    assert "--kubeconfig" in call_args
                    assert "installCRDs=true" in " ".join(call_args)

        assert found_upgrade


@pytest.mark.asyncio
async def test_install_cnpg():
    from mindweaver.service.k8s_cluster.model import K8sCluster, K8sClusterType

    cluster = K8sCluster(
        name="test-cluster-cnpg",
        title="Test Cluster CNPG",
        type=K8sClusterType.REMOTE,
        kubeconfig="fake-kubeconfig",
    )

    mock_svc = MagicMock()
    mock_svc.kubeconfig = pytest.importorskip("unittest.mock").AsyncMock(
        return_value="fake-kubeconfig"
    )

    from mindweaver.service.k8s_cluster.actions import InstallCNPGAction

    with patch("asyncio.create_subprocess_exec") as mock_exec:
        mock_proc = MagicMock()
        mock_proc.returncode = 0
        mock_proc.communicate = pytest.importorskip("unittest.mock").AsyncMock(
            return_value=(b"success", b"")
        )
        mock_exec.return_value = mock_proc

        action = InstallCNPGAction(cluster, mock_svc)
        await action.run()

        # Verify helm repo add
        # Verify helm upgrade --install
        assert mock_exec.call_count >= 3  # add, update, upgrade

        calls = [call[0] for call in mock_exec.call_args_list]
        found_upgrade = False
        for call_args in calls:
            if "upgrade" in call_args and "--install" in call_args:
                if "cnpg" in call_args:
                    found_upgrade = True
                    assert "cnpg/cloudnative-pg" in call_args
                    assert "--kubeconfig" in call_args

        assert found_upgrade


def test_poll_k8s_cluster_error(client: TestClient):

    with patch(
        "mindweaver.service.k8s_cluster.service.config.load_incluster_config",
        side_effect=Exception("K8S Error"),
    ):
        # Create cluster
        p1 = client.post(
            "/api/v1/k8s_clusters",
            json={
                "name": "error-test",
                "title": "Error Test",
                "type": "in-cluster",
            },
        ).json()["data"]

        # Trigger refresh
        client.post(f"/api/v1/k8s_clusters/{p1['id']}/_refresh")

        # Check state
        resp_state = client.get(f"/api/v1/k8s_clusters/{p1['id']}/_state")
        data = resp_state.json()
        assert data["status"] == "error"
        assert data["message"] == "K8S Error"


def test_install_argocd_action_triggers_task(client: TestClient):
    # Create cluster
    p1 = client.post(
        "/api/v1/k8s_clusters",
        json={
            "name": "task-test",
            "title": "Task Test",
            "type": "in-cluster",
        },
    ).json()["data"]

    with patch(
        "mindweaver.tasks.k8s_cluster_status.install_argocd_task.delay"
    ) as mock_delay:
        resp = client.post(
            f"/api/v1/k8s_clusters/{p1['id']}/_actions",
            json={"action": "install_argocd"},
        )
        assert resp.status_code == 200
        assert (
            resp.json()["message"]
            == "ArgoCD installation triggered and status being refreshed."
        )
        mock_delay.assert_called_once_with(p1["id"])

        # Verify status updated immediately in DB
        resp_state = client.get(f"/api/v1/k8s_clusters/{p1['id']}/_state")
        assert resp_state.json()["argocd_installed"] is True
