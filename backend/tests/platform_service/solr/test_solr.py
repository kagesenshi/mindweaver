# SPDX-FileCopyrightText: Copyright © 2026 Mohd Izhar Firdaus Bin Ismail
# SPDX-License-Identifier: AGPLv3+

import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from fastapi import Request
from pydantic import ValidationError
from mindweaver.platform_service.solr import SolrPlatform, SolrPlatformService
from mindweaver.platform_service.zookeeper.model import ZookeeperPlatform, ZookeeperPlatformState
from mindweaver.fw.model import AsyncSession


@pytest.fixture
def mock_service_dependencies():
    request = MagicMock(spec=Request)
    session = MagicMock(spec=AsyncSession)
    session.exec = AsyncMock()
    session.flush = AsyncMock()
    return request, session


def test_solr_resource_defaults():
    """Test default values for Solr resource limits and replicas"""
    model = SolrPlatform(name="test-solr", title="Test Solr", project_id=1)
    assert model.replica_count == 1
    assert model.storage_size == "10Gi"
    assert model.cpu_request == 1.0
    assert model.cpu_limit == 2.0
    assert model.mem_request == 2.0
    assert model.mem_limit == 4.0


def test_solr_validation():
    """Test validation logic for Solr CPU request vs limit and replica count"""
    # CPU invalid case
    with pytest.raises(ValidationError) as excinfo:
        SolrPlatform.model_validate(
            {
                "name": "test-solr",
                "title": "Test Solr",
                "project_id": 1,
                "cpu_request": 3.0,
                "cpu_limit": 2.0,
            }
        )
    assert "CPU request cannot be greater than CPU limit" in str(excinfo.value)

    # Valid replica count cases
    for valid_replicas in [1, 2, 3, 5, 9]:
        model = SolrPlatform.model_validate(
            {
                "name": "test-solr",
                "title": "Test Solr",
                "project_id": 1,
                "replica_count": valid_replicas,
            }
        )
        assert model.replica_count == valid_replicas

    # Invalid replica count cases
    for invalid_replicas in [0, 10]:
        with pytest.raises(ValidationError) as excinfo:
            SolrPlatform.model_validate(
                {
                    "name": "test-solr",
                    "title": "Test Solr",
                    "project_id": 1,
                    "replica_count": invalid_replicas,
                }
            )
        assert "Replica count must be between 1 and 9" in str(excinfo.value)


@pytest.mark.asyncio
async def test_solr_template_vars(mock_service_dependencies):
    """Test that template_vars returns expected variables without external ZK."""
    request, session = mock_service_dependencies
    svc = SolrPlatformService(request, session)

    model = SolrPlatform(
        name="test-solr",
        project_id=1,
        admin_password="my-admin-password",
    )

    svc._resolve_namespace = AsyncMock(return_value="test-ns")
    svc.project = AsyncMock(return_value=MagicMock(ingress_domain=None))

    # Resolve variables
    vars = await svc.template_vars(model)

    assert vars["name"] == "test-solr"
    assert vars["namespace"] == "test-ns"
    assert vars["admin_password"] == "my-admin-password"
    assert vars["replica_count"] == 1
    assert vars["zookeeper_connection_string"] is None


@pytest.mark.asyncio
async def test_solr_template_vars_with_external_zk(mock_service_dependencies):
    """Test that template_vars reads zookeeper_url from ZK state (not constructed)."""
    request, session = mock_service_dependencies
    svc = SolrPlatformService(request, session)

    model = SolrPlatform(
        name="test-solr",
        project_id=1,
        zookeeper_id=42,
    )

    svc._resolve_namespace = AsyncMock(return_value="test-ns")
    svc.project = AsyncMock(return_value=MagicMock(ingress_domain=None))

    zk_model = ZookeeperPlatform(id=42, name="myzk", project_id=1)
    zk_state = MagicMock(spec=ZookeeperPlatformState)
    zk_state.active = True
    zk_state.zookeeper_url = "myzk-zookeeper-client.myzk-ns.svc.cluster.local:2181"

    mock_zk_svc = MagicMock()
    mock_zk_svc.get = AsyncMock(return_value=zk_model)
    mock_zk_svc.platform_state = AsyncMock(return_value=zk_state)

    with patch(
        "mindweaver.platform_service.solr.service.ZookeeperPlatformService.get_service",
        AsyncMock(return_value=mock_zk_svc)
    ):
        vars = await svc.template_vars(model)

    # The connection string must come from state, not be constructed locally
    assert vars["zookeeper_connection_string"] == "myzk-zookeeper-client.myzk-ns.svc.cluster.local:2181"


@pytest.mark.asyncio
async def test_solr_template_vars_zk_not_polled(mock_service_dependencies):
    """Test that template_vars raises a clear error when ZK state has no URL yet."""
    request, session = mock_service_dependencies
    svc = SolrPlatformService(request, session)

    model = SolrPlatform(name="test-solr", project_id=1, zookeeper_id=42)

    svc._resolve_namespace = AsyncMock(return_value="test-ns")
    svc.project = AsyncMock(return_value=MagicMock(ingress_domain=None))

    zk_model = ZookeeperPlatform(id=42, name="myzk", project_id=1)
    zk_state = MagicMock(spec=ZookeeperPlatformState)
    zk_state.active = True
    zk_state.zookeeper_url = None  # Not yet polled

    mock_zk_svc = MagicMock()
    mock_zk_svc.get = AsyncMock(return_value=zk_model)
    mock_zk_svc.platform_state = AsyncMock(return_value=zk_state)

    with patch(
        "mindweaver.platform_service.solr.service.ZookeeperPlatformService.get_service",
        AsyncMock(return_value=mock_zk_svc)
    ):
        with pytest.raises(ValueError, match="has not been polled yet"):
            await svc.template_vars(model)


@pytest.mark.asyncio
async def test_solr_render_manifests(mock_service_dependencies):
    """Test that manifests render correctly for Solr"""
    request, session = mock_service_dependencies
    svc = SolrPlatformService(request, session)

    model = SolrPlatform(
        name="solr-test",
        project_id=1,
        replica_count=1,
        admin_password="pass",
    )
    svc._resolve_namespace = AsyncMock(return_value="test-ns")
    svc.project = AsyncMock(return_value=MagicMock(ingress_domain=None))

    manifests = await svc.render_manifests(model)
    assert "replicas: 1" in manifests
    assert "authenticationType: \"Basic\"" in manifests
    assert "zk:" in manifests
    assert "provided:" in manifests


@pytest.mark.asyncio
async def test_solr_poll_status(mock_service_dependencies):
    """Test that solr_url is derived correctly in poll_status"""
    from mindweaver.platform_service.solr.model import SolrPlatformState
    request, session = mock_service_dependencies
    svc = SolrPlatformService(request, session)

    model = SolrPlatform(
        name="solr-test",
        project_id=1,
    )

    mock_state = MagicMock(spec=SolrPlatformState)
    mock_state.active = True

    with patch.object(svc, "platform_state", AsyncMock(return_value=mock_state)), \
         patch.object(svc, "kubeconfig", AsyncMock(return_value="mock-kubeconfig")), \
         patch.object(svc, "_resolve_namespace", AsyncMock(return_value="test-ns")):

        node_ports = [{"name": "solr-test", "port": 8983, "node_port": 30001}]
        cluster_nodes = [{"hostname": "node1", "ipv4": "1.2.3.4", "ipv6": None}]

        async def mock_poll(*args):
            return "online", "Healthy", {}, node_ports, cluster_nodes, "solr-test-solrcloud-common", "mock-pass", "mock-k8soper-pass", "mock-solr-pass"

        with patch("mindweaver.platform_service.solr.service.asyncio.to_thread", side_effect=mock_poll), \
             patch("mindweaver.platform_service.solr.service.decrypt_password", side_effect=lambda x: x), \
             patch("mindweaver.platform_service.solr.service.encrypt_password", side_effect=lambda x: x):
            
            # 1. Test without ingress_domain (should derive NodePort URL)
            mock_project_no_ingress = MagicMock()
            mock_project_no_ingress.ingress_domain = None
            svc.project = AsyncMock(return_value=mock_project_no_ingress)

            await svc.poll_status(model)
            assert mock_state.solr_url == "https://1.2.3.4:30001"
            assert mock_state.admin_password == "mock-pass"
            assert mock_state.k8s_oper_password == "mock-k8soper-pass"
            assert mock_state.solr_user_password == "mock-solr-pass"

            # 2. Test with ingress_domain (should derive secure Ingress URL)
            mock_project_ingress = MagicMock()
            mock_project_ingress.ingress_domain = "132.home.kagesenshi.org"
            svc.project = AsyncMock(return_value=mock_project_ingress)

            await svc.poll_status(model)
            assert mock_state.solr_url == "https://solr-test.132.home.kagesenshi.org"
            assert mock_state.solr_url_ipv6 is None
            assert mock_state.extra_data["ingress_domain"] == "132.home.kagesenshi.org"


@pytest.mark.asyncio
async def test_solr_poll_status_service_selection_nodeport_exclusion(mock_service_dependencies):
    """Test that poll_status excludes the -nodeport service and resolves the -headless service."""
    from mindweaver.platform_service.solr.model import SolrPlatformState
    request, session = mock_service_dependencies
    svc = SolrPlatformService(request, session)

    model = SolrPlatform(
        name="solr-test",
        project_id=1,
    )

    mock_state = MagicMock(spec=SolrPlatformState)
    mock_state.active = True

    # Mock Services returned by Kubernetes API
    mock_headless_svc = MagicMock()
    mock_headless_svc.metadata.name = "solr-test-solrcloud-headless"
    mock_headless_svc.metadata.labels = {"solrcloud": "solr-test"}
    mock_headless_port = MagicMock()
    mock_headless_port.port = 8983
    mock_headless_svc.spec.ports = [mock_headless_port]
    mock_headless_svc.spec.cluster_ip = "None"
    mock_headless_svc.spec.type = "ClusterIP"

    mock_nodeport_svc = MagicMock()
    mock_nodeport_svc.metadata.name = "solr-test-nodeport"
    mock_nodeport_svc.metadata.labels = {"solrcloud": "solr-test"}
    mock_nodeport_port = MagicMock()
    mock_nodeport_port.port = 8983
    mock_nodeport_port.node_port = 30001
    mock_nodeport_svc.spec.ports = [mock_nodeport_port]
    mock_nodeport_svc.spec.cluster_ip = "10.96.0.11"
    mock_nodeport_svc.spec.type = "NodePort"

    mock_services_list = MagicMock()
    mock_services_list.items = [mock_headless_svc, mock_nodeport_svc]

    # Mock K8s Client responses
    mock_core_v1 = MagicMock()
    mock_core_v1.list_namespaced_pod.return_value = MagicMock(items=[])
    mock_core_v1.list_namespaced_service.return_value = mock_services_list
    mock_core_v1.list_node.return_value = MagicMock(items=[])
    mock_core_v1.read_namespaced_secret.side_effect = Exception("No secret")

    mock_custom_api = MagicMock()
    mock_custom_api.get_namespaced_custom_object.return_value = {
        "status": {"sync": {"status": "Synced"}, "health": {"status": "Healthy"}}
    }

    with patch.object(svc, "platform_state", AsyncMock(return_value=mock_state)), \
         patch.object(svc, "kubeconfig", AsyncMock(return_value="mock-kubeconfig")), \
         patch.object(svc, "_resolve_namespace", AsyncMock(return_value="test-ns")), \
         patch("mindweaver.platform_service.solr.service.config.new_client_from_config"), \
         patch("mindweaver.platform_service.solr.service.client.CoreV1Api", return_value=mock_core_v1), \
         patch("mindweaver.platform_service.solr.service.client.CustomObjectsApi", return_value=mock_custom_api):

        # Test project without ingress
        mock_project = MagicMock()
        mock_project.ingress_domain = None
        svc.project = AsyncMock(return_value=mock_project)

        await svc.poll_status(model)

        # Verify that the service_name in extra_data matches the headless service, not the nodeport service
        assert mock_state.extra_data["service_name"] == "solr-test-solrcloud-headless"
        # The internal URL should also be derived from the headless service
        assert mock_state.solr_internal_url == "https://solr-test-solrcloud-headless.test-ns.svc.cluster.local:8983"
        # Verify that the NodePort service port was collected
        assert len(mock_state.node_ports) == 1
        assert mock_state.node_ports[0]["name"] == "solr-test-nodeport"
        assert mock_state.node_ports[0]["node_port"] == 30001




@pytest.mark.asyncio
async def test_solr_poll_status_all_credentials_fetched(mock_service_dependencies):
    """Test that admin/solr passwords are read from bootstrap secret and k8s-oper from basic-auth secret."""
    import base64
    from mindweaver.platform_service.solr.model import SolrPlatformState

    request, session = mock_service_dependencies
    svc = SolrPlatformService(request, session)

    model = SolrPlatform(name="solr-test", project_id=1)
    mock_state = MagicMock(spec=SolrPlatformState)
    mock_state.active = True

    def _b64(s):
        return base64.b64encode(s.encode()).decode()

    mock_bootstrap_secret = MagicMock()
    mock_bootstrap_secret.data = {
        "admin": _b64("admin-secret"),
        "solr": _b64("solruser-secret"),
        "security.json": _b64("{}"),
    }

    mock_basic_auth_secret = MagicMock()
    mock_basic_auth_secret.data = {
        "username": _b64("k8s-oper"),
        "password": _b64("k8soper-secret"),
    }

    def _read_secret(name, namespace):
        if name.endswith("-solrcloud-security-bootstrap"):
            return mock_bootstrap_secret
        if name.endswith("-solrcloud-basic-auth"):
            return mock_basic_auth_secret
        raise Exception(f"Unexpected secret: {name}")

    mock_core_v1 = MagicMock()
    mock_core_v1.list_namespaced_pod.return_value = MagicMock(items=[])
    mock_core_v1.list_namespaced_service.return_value = MagicMock(items=[])
    mock_core_v1.list_node.return_value = MagicMock(items=[])
    mock_core_v1.read_namespaced_secret.side_effect = _read_secret

    mock_custom_api = MagicMock()
    mock_custom_api.get_namespaced_custom_object.return_value = {
        "status": {"sync": {"status": "Synced"}, "health": {"status": "Healthy"}}
    }

    with patch.object(svc, "platform_state", AsyncMock(return_value=mock_state)), \
         patch.object(svc, "kubeconfig", AsyncMock(return_value="mock-kubeconfig")), \
         patch.object(svc, "_resolve_namespace", AsyncMock(return_value="test-ns")), \
         patch("mindweaver.platform_service.solr.service.config.new_client_from_config"), \
         patch("mindweaver.platform_service.solr.service.client.CoreV1Api", return_value=mock_core_v1), \
         patch("mindweaver.platform_service.solr.service.client.CustomObjectsApi", return_value=mock_custom_api), \
         patch("mindweaver.platform_service.solr.service.encrypt_password", side_effect=lambda x: x):

        mock_project = MagicMock()
        mock_project.ingress_domain = None
        svc.project = AsyncMock(return_value=mock_project)

        await svc.poll_status(model)

    # admin and solr come from bootstrap secret; k8s-oper from basic-auth secret
    assert mock_state.admin_password == "admin-secret"
    assert mock_state.k8s_oper_password == "k8soper-secret"
    assert mock_state.solr_user_password == "solruser-secret"


@pytest.mark.asyncio
async def test_solr_poll_status_missing_credentials_not_overwritten(mock_service_dependencies):
    """Test that when secrets are missing/absent the existing state values are preserved."""
    import base64
    from mindweaver.platform_service.solr.model import SolrPlatformState

    request, session = mock_service_dependencies
    svc = SolrPlatformService(request, session)

    model = SolrPlatform(name="solr-test", project_id=1)
    mock_state = MagicMock(spec=SolrPlatformState)
    mock_state.active = True
    existing_k8s_oper = "existing-k8soper"
    existing_solr_user = "existing-solruser"
    mock_state.k8s_oper_password = existing_k8s_oper
    mock_state.solr_user_password = existing_solr_user

    def _b64(s):
        return base64.b64encode(s.encode()).decode()

    # Bootstrap secret only has admin; basic-auth secret is absent (raises exception)
    mock_bootstrap_secret = MagicMock()
    mock_bootstrap_secret.data = {
        "admin": _b64("new-admin"),
    }

    def _read_secret(name, namespace):
        if name.endswith("-solrcloud-security-bootstrap"):
            return mock_bootstrap_secret
        # basic-auth secret is not yet available
        raise Exception(f"Not found: {name}")

    mock_core_v1 = MagicMock()
    mock_core_v1.list_namespaced_pod.return_value = MagicMock(items=[])
    mock_core_v1.list_namespaced_service.return_value = MagicMock(items=[])
    mock_core_v1.list_node.return_value = MagicMock(items=[])
    mock_core_v1.read_namespaced_secret.side_effect = _read_secret

    mock_custom_api = MagicMock()
    mock_custom_api.get_namespaced_custom_object.return_value = {
        "status": {"sync": {"status": "Synced"}, "health": {"status": "Healthy"}}
    }

    with patch.object(svc, "platform_state", AsyncMock(return_value=mock_state)), \
         patch.object(svc, "kubeconfig", AsyncMock(return_value="mock-kubeconfig")), \
         patch.object(svc, "_resolve_namespace", AsyncMock(return_value="test-ns")), \
         patch("mindweaver.platform_service.solr.service.config.new_client_from_config"), \
         patch("mindweaver.platform_service.solr.service.client.CoreV1Api", return_value=mock_core_v1), \
         patch("mindweaver.platform_service.solr.service.client.CustomObjectsApi", return_value=mock_custom_api), \
         patch("mindweaver.platform_service.solr.service.encrypt_password", side_effect=lambda x: x):

        mock_project = MagicMock()
        mock_project.ingress_domain = None
        svc.project = AsyncMock(return_value=mock_project)

        await svc.poll_status(model)

    # admin updated from bootstrap; k8s-oper and solr-user remain at pre-existing values
    assert mock_state.admin_password == "new-admin"
    assert mock_state.k8s_oper_password == existing_k8s_oper
    assert mock_state.solr_user_password == existing_solr_user
