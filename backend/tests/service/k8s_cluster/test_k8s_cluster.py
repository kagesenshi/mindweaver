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

        # Mock Pods (Envoy Gateway version)
        mock_pod_eg = MagicMock()
        mock_pod_eg.metadata.labels = {"app.kubernetes.io/version": "v1.0.0"}
        mock_pod_eg.spec.containers = [MagicMock(image="envoyproxy/gateway:v1.0.0")]

        # Mock Pods (Solr Operator version)
        mock_pod_solr = MagicMock()
        mock_pod_solr.metadata.labels = {"app.kubernetes.io/version": "v0.9.1"}
        mock_pod_solr.spec.containers = [MagicMock(image="solr-operator:v0.9.1")]

        # Mock Pods (Kafka Operator version)
        mock_pod_kafka = MagicMock()
        mock_pod_kafka.metadata.labels = {"app.kubernetes.io/version": "v0.41.0"}
        mock_pod_kafka.spec.containers = [MagicMock(image="strimzi/operator:v0.41.0")]

        # Mock Pods (NiFiKop Operator version)
        mock_pod_nifikop = MagicMock()
        mock_pod_nifikop.metadata.labels = {"app.kubernetes.io/version": "v1.17.0"}
        mock_pod_nifikop.spec.containers = [MagicMock(image="konpyutaika/nifikop:v1.17.0")]

        def _mock_list_pod_for_all_namespaces(label_selector=None):
            m_list = MagicMock()
            if "argocd-server" in label_selector:
                m_list.items = [mock_pod_argo]
            elif "cert-manager" in label_selector:
                m_list.items = [mock_pod_cm]
            elif "cloudnative-pg" in label_selector:
                m_list.items = [mock_pod_cnpg]
            elif "envoy-gateway" in label_selector:
                m_list.items = [mock_pod_eg]
            elif "solr-operator" in label_selector:
                m_list.items = [mock_pod_solr]
            elif "strimzi-kafka-operator" in label_selector or "kafka-operator" in label_selector or "name=strimzi-cluster-operator" in label_selector or "strimzi.io/kind=cluster-operator" in label_selector:
                m_list.items = [mock_pod_kafka]
            elif "nifikop" in label_selector:
                m_list.items = [mock_pod_nifikop]
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
        mock_secret_eg = MagicMock()
        mock_secret_eg.metadata.name = "sh.helm.release.v1.eg.v1"
        mock_secret_solr = MagicMock()
        mock_secret_solr.metadata.name = "sh.helm.release.v1.solr-operator.v1"
        mock_secret_kafka = MagicMock()
        mock_secret_kafka.metadata.name = "sh.helm.release.v1.strimzi-kafka-operator.v1"
        mock_secret_nifikop = MagicMock()
        mock_secret_nifikop.metadata.name = "sh.helm.release.v1.nifikop.v1"

        mock_secret_list = MagicMock()
        mock_secret_list.items = [
            mock_secret_argo,
            mock_secret_cm,
            mock_secret_cnpg,
            mock_secret_eg,
            mock_secret_nifikop,
        ]
        mock_core.return_value.list_secret_for_all_namespaces.return_value = (
            mock_secret_list
        )

        yield {"core": mock_core, "version": mock_version}


@pytest.fixture(autouse=True)
def mock_get_kubernetes_clients():
    with patch(
        "mindweaver.service.k8s_cluster.actions.InstallArgoCDAction._get_kubernetes_clients"
    ) as mock_clients:
        mock_core = MagicMock()
        mock_ext = MagicMock()
        mock_clients.return_value = (mock_core, mock_ext)
        yield mock_clients


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
    assert data["envoy_gateway_installed"] is True
    assert data["envoy_gateway_version"] == "v1.0.0"
    assert data["solr_operator_installed"] is True
    assert data["solr_operator_version"] == "v0.9.1"
    assert data["kafka_operator_installed"] is True
    assert data["kafka_operator_version"] == "v0.41.0"
    assert data["nifikop_installed"] is True
    assert data["nifikop_version"] == "v1.17.0"


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
    import os

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

    applied_manifests = []

    def mock_subprocess(*args, **kwargs):
        cmd = args
        if len(cmd) > 0 and "kubectl" in cmd:
            path = cmd[-1]
            if os.path.exists(path):
                with open(path, "r") as f:
                    applied_manifests.append(f.read())
        mock_proc = MagicMock()
        mock_proc.returncode = 0
        mock_proc.communicate = pytest.importorskip("unittest.mock").AsyncMock(
            return_value=(b"success", b"")
        )
        return mock_proc

    with patch("asyncio.create_subprocess_exec", side_effect=mock_subprocess) as mock_exec:
        action = InstallCertManagerAction(cluster, mock_svc)
        await action.run()

        assert len(applied_manifests) == 1
        manifest = applied_manifests[0]
        assert "kind: Application" in manifest
        assert "name: cert-manager" in manifest
        assert "repoURL: https://charts.jetstack.io" in manifest
        assert "chart: cert-manager" in manifest
        assert "targetRevision: v1.20.0" in manifest
        assert "installCRDs: true" in manifest


@pytest.mark.asyncio
async def test_install_cnpg():
    from mindweaver.service.k8s_cluster.model import K8sCluster, K8sClusterType
    import os

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

    applied_manifests = []

    def mock_subprocess(*args, **kwargs):
        cmd = args
        if len(cmd) > 0 and "kubectl" in cmd:
            path = cmd[-1]
            if os.path.exists(path):
                with open(path, "r") as f:
                    applied_manifests.append(f.read())
        mock_proc = MagicMock()
        mock_proc.returncode = 0
        mock_proc.communicate = pytest.importorskip("unittest.mock").AsyncMock(
            return_value=(b"success", b"")
        )
        return mock_proc

    with patch("asyncio.create_subprocess_exec", side_effect=mock_subprocess) as mock_exec:
        action = InstallCNPGAction(cluster, mock_svc)
        await action.run()

        assert len(applied_manifests) == 1
        manifest = applied_manifests[0]
        assert "kind: Application" in manifest
        assert "name: cnpg" in manifest
        assert "repoURL: https://cloudnative-pg.github.io/charts" in manifest
        assert "chart: cloudnative-pg" in manifest
        assert "targetRevision: 0.27.1" in manifest


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


@pytest.mark.asyncio
async def test_install_envoy_gateway():
    from mindweaver.service.k8s_cluster.model import K8sCluster, K8sClusterType
    import os

    cluster = K8sCluster(
        name="test-cluster-eg",
        title="Test Cluster EG",
        type=K8sClusterType.REMOTE,
        kubeconfig="fake-kubeconfig",
    )

    mock_svc = MagicMock()
    mock_svc.kubeconfig = pytest.importorskip("unittest.mock").AsyncMock(
        return_value="fake-kubeconfig"
    )

    from mindweaver.service.k8s_cluster.actions import InstallEnvoyGatewayAction

    applied_manifests = []

    def mock_subprocess(*args, **kwargs):
        cmd = args
        if len(cmd) > 0 and "kubectl" in cmd:
            path = cmd[-1]
            if os.path.exists(path):
                with open(path, "r") as f:
                    applied_manifests.append(f.read())
        mock_proc = MagicMock()
        mock_proc.returncode = 0
        mock_proc.communicate = pytest.importorskip("unittest.mock").AsyncMock(
            return_value=(b"success", b"")
        )
        return mock_proc

    with patch("asyncio.create_subprocess_exec", side_effect=mock_subprocess) as mock_exec:
        action = InstallEnvoyGatewayAction(cluster, mock_svc)
        await action.run()

        # Verify that kubectl apply applied the Envoy Gateway Application and the global GatewayClass/EnvoyProxy config
        assert len(applied_manifests) == 2

        # Manifest 1: ArgoCD Application
        app_manifest = applied_manifests[0]
        assert "kind: Application" in app_manifest
        assert "name: envoy-gateway" in app_manifest
        assert "repoURL: docker.io/envoyproxy" in app_manifest
        assert "chart: gateway-helm" in app_manifest
        assert "targetRevision: 1.8.1" in app_manifest

        # Manifest 2: Envoy Gateway configuration
        config_manifest = applied_manifests[1]
        assert "kind: GatewayClass" in config_manifest
        assert "kind: EnvoyProxy" in config_manifest


def test_install_envoy_gateway_action_triggers_task(client: TestClient):
    # Create cluster
    p1 = client.post(
        "/api/v1/k8s_clusters",
        json={
            "name": "task-test-eg",
            "title": "Task Test EG",
            "type": "in-cluster",
        },
    ).json()["data"]

    with patch(
        "mindweaver.tasks.k8s_cluster_status.install_envoy_gateway_task.delay"
    ) as mock_delay:
        resp = client.post(
            f"/api/v1/k8s_clusters/{p1['id']}/_actions",
            json={"action": "install_envoy_gateway"},
        )
        assert resp.status_code == 200
        assert (
            resp.json()["message"]
            == "Envoy Gateway installation triggered and status being refreshed."
        )
        mock_delay.assert_called_once_with(p1["id"])

        # Verify status updated immediately in DB
        resp_state = client.get(f"/api/v1/k8s_clusters/{p1['id']}/_state")
        assert resp_state.json()["envoy_gateway_installed"] is True


def test_sync_core_integrations_action_triggers_task(client: TestClient):
    # Create cluster
    p1 = client.post(
        "/api/v1/k8s_clusters",
        json={
            "name": "task-test-sync",
            "title": "Task Test Sync",
            "type": "in-cluster",
            "envoy_gateway_service_type": "LoadBalancer",
        },
    ).json()["data"]

    with patch(
        "mindweaver.tasks.k8s_cluster_status.sync_core_integrations_task.delay"
    ) as mock_delay:
        resp = client.post(
            f"/api/v1/k8s_clusters/{p1['id']}/_actions",
            json={"action": "sync_core_integrations"},
        )
        assert resp.status_code == 200
        assert (
            resp.json()["message"]
            == "Core integrations synchronization triggered."
        )
        mock_delay.assert_called_once_with(p1["id"])


@pytest.mark.asyncio
async def test_install_envoy_gateway_with_loadbalancer():
    from mindweaver.service.k8s_cluster.model import K8sCluster, K8sClusterType, EnvoyGatewayServiceType
    import os

    cluster = K8sCluster(
        name="test-cluster-eg-lb",
        title="Test Cluster EG LB",
        type=K8sClusterType.REMOTE,
        kubeconfig="fake-kubeconfig",
        envoy_gateway_service_type=EnvoyGatewayServiceType.LOAD_BALANCER,
    )

    mock_svc = MagicMock()
    mock_svc.kubeconfig = pytest.importorskip("unittest.mock").AsyncMock(
        return_value="fake-kubeconfig"
    )

    from mindweaver.service.k8s_cluster.actions import InstallEnvoyGatewayAction

    applied_manifests = []

    def mock_subprocess(*args, **kwargs):
        cmd = args
        if len(cmd) > 0 and "kubectl" in cmd:
            path = cmd[-1]
            if os.path.exists(path):
                with open(path, "r") as f:
                    applied_manifests.append(f.read())
        mock_proc = MagicMock()
        mock_proc.returncode = 0
        mock_proc.communicate = pytest.importorskip("unittest.mock").AsyncMock(
            return_value=(b"success", b"")
        )
        return mock_proc

    with patch("asyncio.create_subprocess_exec", side_effect=mock_subprocess) as mock_exec:
        action = InstallEnvoyGatewayAction(cluster, mock_svc)
        await action.run()

        # Verify that kubectl apply applied both the Application and EnvoyProxy LoadBalancer type
        assert len(applied_manifests) == 2
        config_manifest = applied_manifests[1]
        assert "type: LoadBalancer" in config_manifest


@pytest.mark.asyncio
async def test_install_solr_operator():
    from mindweaver.service.k8s_cluster.model import K8sCluster, K8sClusterType
    import os

    cluster = K8sCluster(
        name="test-cluster-solr-op",
        title="Test Cluster Solr Op",
        type=K8sClusterType.REMOTE,
        kubeconfig="fake-kubeconfig",
    )

    mock_svc = MagicMock()
    mock_svc.kubeconfig = pytest.importorskip("unittest.mock").AsyncMock(
        return_value="fake-kubeconfig"
    )

    from mindweaver.service.k8s_cluster.actions import InstallSolrOperatorAction

    applied_manifests = []

    def mock_subprocess(*args, **kwargs):
        cmd = args
        if len(cmd) > 0 and "kubectl" in cmd:
            path = cmd[-1]
            if os.path.exists(path):
                with open(path, "r") as f:
                    applied_manifests.append(f.read())
        mock_proc = MagicMock()
        mock_proc.returncode = 0
        mock_proc.communicate = pytest.importorskip("unittest.mock").AsyncMock(
            return_value=(b"success", b"")
        )
        return mock_proc

    with patch("asyncio.create_subprocess_exec", side_effect=mock_subprocess) as mock_exec:
        action = InstallSolrOperatorAction(cluster, mock_svc)
        await action.run()

        assert len(applied_manifests) == 1
        manifest = applied_manifests[0]
        assert "kind: Application" in manifest
        assert "name: solr-operator" in manifest
        assert "repoURL: https://solr.apache.org/charts" in manifest
        assert "chart: solr-operator" in manifest
        assert "targetRevision: 0.9.1" in manifest
        assert "installCRDs: true" in manifest
        assert "zookeeper-operator" in manifest


@pytest.mark.asyncio
async def test_install_kafka_operator():
    from mindweaver.service.k8s_cluster.model import K8sCluster, K8sClusterType
    import os

    cluster = K8sCluster(
        name="test-cluster-kafka-op",
        title="Test Cluster Kafka Op",
        type=K8sClusterType.REMOTE,
        kubeconfig="fake-kubeconfig",
    )

    mock_svc = MagicMock()
    mock_svc.kubeconfig = pytest.importorskip("unittest.mock").AsyncMock(
        return_value="fake-kubeconfig"
    )

    from mindweaver.service.k8s_cluster.actions import InstallKafkaOperatorAction

    applied_manifests = []

    def mock_subprocess(*args, **kwargs):
        cmd = args
        if len(cmd) > 0 and "kubectl" in cmd:
            path = cmd[-1]
            if os.path.exists(path):
                with open(path, "r") as f:
                    applied_manifests.append(f.read())
        mock_proc = MagicMock()
        mock_proc.returncode = 0
        mock_proc.communicate = pytest.importorskip("unittest.mock").AsyncMock(
            return_value=(b"success", b"")
        )
        return mock_proc

    with patch("asyncio.create_subprocess_exec", side_effect=mock_subprocess) as mock_exec:
        action = InstallKafkaOperatorAction(cluster, mock_svc)
        await action.run()

        assert len(applied_manifests) == 1
        manifest = applied_manifests[0]
        assert "kind: Application" in manifest
        assert "name: kafka-operator" in manifest
        assert "repoURL: https://strimzi.io/charts/" in manifest
        assert "chart: strimzi-kafka-operator" in manifest
        assert "targetRevision: 0.41.0" in manifest


@pytest.mark.asyncio
async def test_install_nifikop():
    from mindweaver.service.k8s_cluster.model import K8sCluster, K8sClusterType
    import os

    cluster = K8sCluster(
        name="test-cluster-nifikop-op",
        title="Test Cluster NiFiKop Op",
        type=K8sClusterType.REMOTE,
        kubeconfig="fake-kubeconfig",
    )

    mock_svc = MagicMock()
    mock_svc.kubeconfig = pytest.importorskip("unittest.mock").AsyncMock(
        return_value="fake-kubeconfig"
    )

    from mindweaver.service.k8s_cluster.actions import InstallNifikopAction

    applied_manifests = []

    def mock_subprocess(*args, **kwargs):
        cmd = args
        if len(cmd) > 0 and "kubectl" in cmd:
            path = cmd[-1]
            if os.path.exists(path):
                with open(path, "r") as f:
                    applied_manifests.append(f.read())
        mock_proc = MagicMock()
        mock_proc.returncode = 0
        mock_proc.communicate = pytest.importorskip("unittest.mock").AsyncMock(
            return_value=(b"success", b"")
        )
        return mock_proc

    with patch("asyncio.create_subprocess_exec", side_effect=mock_subprocess) as mock_exec:
        action = InstallNifikopAction(cluster, mock_svc)
        await action.run()

        assert len(applied_manifests) == 1
        manifest = applied_manifests[0]
        assert "kind: Application" in manifest
        assert "name: nifikop-operator" in manifest
        assert "repoURL: ghcr.io/konpyutaika/helm-charts" in manifest
        assert "chart: nifikop" in manifest
        assert "targetRevision: 1.17.0" in manifest


def test_install_nifikop_action_triggers_task(client: TestClient):
    # Create cluster
    p1 = client.post(
        "/api/v1/k8s_clusters",
        json={
            "name": "task-test-nifikop",
            "title": "Task Test NiFiKop",
            "type": "in-cluster",
        },
    ).json()["data"]

    with patch(
        "mindweaver.tasks.k8s_cluster_status.install_nifikop_task.delay"
    ) as mock_delay:
        resp = client.post(
            f"/api/v1/k8s_clusters/{p1['id']}/_actions",
            json={"action": "install_nifikop"},
        )
        assert resp.status_code == 200
        assert (
            resp.json()["message"]
            == "NiFiKop Operator installation triggered and status being refreshed."
        )
        mock_delay.assert_called_once_with(p1["id"])

        # Verify status updated immediately in DB
        resp_state = client.get(f"/api/v1/k8s_clusters/{p1['id']}/_state")
        assert resp_state.json()["nifikop_installed"] is True





