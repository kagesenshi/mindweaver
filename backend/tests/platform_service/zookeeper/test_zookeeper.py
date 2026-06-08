# SPDX-FileCopyrightText: Copyright © 2026 Mohd Izhar Firdaus Bin Ismail
# SPDX-License-Identifier: AGPLv3+

import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from fastapi import Request
from pydantic import ValidationError
from mindweaver.platform_service.zookeeper import ZookeeperPlatform, ZookeeperPlatformService
from mindweaver.fw.model import AsyncSession


@pytest.fixture
def mock_service_dependencies():
    request = MagicMock(spec=Request)
    session = MagicMock(spec=AsyncSession)
    session.exec = AsyncMock()
    session.flush = AsyncMock()
    return request, session


def test_zookeeper_resource_defaults():
    """Test default values for Zookeeper resource limits and replicas."""
    model = ZookeeperPlatform(name="test-zk", title="Test ZK", project_id=1)
    assert model.replica_count == 3
    assert model.storage_size == "20Gi"
    assert model.cpu_request == 0.5
    assert model.cpu_limit == 1.0
    assert model.mem_request == 1.0
    assert model.mem_limit == 2.0
    assert model.chart_version == "0.2.15"


def test_zookeeper_cpu_validation():
    """Test that CPU request cannot exceed CPU limit."""
    with pytest.raises(ValidationError) as excinfo:
        ZookeeperPlatform.model_validate(
            {
                "name": "test-zk",
                "title": "Test ZK",
                "project_id": 1,
                "cpu_request": 4.0,
                "cpu_limit": 2.0,
            }
        )
    assert "CPU request cannot be greater than CPU limit" in str(excinfo.value)


def test_zookeeper_mem_validation():
    """Test that memory request cannot exceed memory limit."""
    with pytest.raises(ValidationError) as excinfo:
        ZookeeperPlatform.model_validate(
            {
                "name": "test-zk",
                "title": "Test ZK",
                "project_id": 1,
                "mem_request": 8.0,
                "mem_limit": 4.0,
            }
        )
    assert "Memory request cannot be greater than Memory limit" in str(excinfo.value)


def test_zookeeper_replica_count_validation():
    """Test that replica count is validated between 1 and 9."""
    # Valid replica counts
    for valid_replicas in [1, 3, 5, 9]:
        model = ZookeeperPlatform.model_validate(
            {
                "name": "test-zk",
                "title": "Test ZK",
                "project_id": 1,
                "replica_count": valid_replicas,
            }
        )
        assert model.replica_count == valid_replicas

    # Invalid replica counts
    for invalid_replicas in [0, 10]:
        with pytest.raises(ValidationError) as excinfo:
            ZookeeperPlatform.model_validate(
                {
                    "name": "test-zk",
                    "title": "Test ZK",
                    "project_id": 1,
                    "replica_count": invalid_replicas,
                }
            )
        assert "Replica count must be between 1 and 9" in str(excinfo.value)


@pytest.mark.asyncio
async def test_zookeeper_template_vars(mock_service_dependencies):
    """Test that template_vars returns expected template variable mappings."""
    request, session = mock_service_dependencies
    svc = ZookeeperPlatformService(request, session)

    model = ZookeeperPlatform(
        name="test-zk",
        project_id=1,
        replica_count=3,
        storage_size="20Gi",
    )

    svc._resolve_namespace = AsyncMock(return_value="test-ns")
    svc.project = AsyncMock(return_value=MagicMock(ingress_domain=None))

    vars = await svc.template_vars(model)

    assert vars["name"] == "test-zk"
    assert vars["namespace"] == "test-ns"
    assert vars["replica_count"] == 3
    assert vars["storage_size"] == "20Gi"


@pytest.mark.asyncio
async def test_zookeeper_render_manifests(mock_service_dependencies):
    """Test that the ArgoCD Application manifests render correctly."""
    request, session = mock_service_dependencies
    svc = ZookeeperPlatformService(request, session)

    model = ZookeeperPlatform(
        name="test-zk",
        project_id=1,
        replica_count=3,
        storage_size="20Gi",
    )

    svc._resolve_namespace = AsyncMock(return_value="test-ns")
    svc.project = AsyncMock(return_value=MagicMock(ingress_domain=None))

    manifests = await svc.render_manifests(model)

    assert "name: test-zk" in manifests
    assert "replicas: 3" in manifests
    assert "chart: zookeeper" in manifests
    assert "charts.pravega.io" in manifests
    assert "volumeSize: \"20Gi\"" in manifests
    assert "namespace: test-ns" in manifests


@pytest.mark.asyncio
async def test_zookeeper_render_manifests_image_override(mock_service_dependencies):
    """Test that image override is rendered correctly when enabled."""
    request, session = mock_service_dependencies
    svc = ZookeeperPlatformService(request, session)

    model = ZookeeperPlatform(
        name="test-zk",
        project_id=1,
        override_image=True,
        image="my-custom/zookeeper",
        image_tag="custom-1.0",
    )

    svc._resolve_namespace = AsyncMock(return_value="test-ns")
    svc.project = AsyncMock(return_value=MagicMock(ingress_domain=None))

    manifests = await svc.render_manifests(model)

    assert "my-custom/zookeeper" in manifests
    assert "custom-1.0" in manifests


@pytest.mark.asyncio
async def test_zookeeper_poll_status(mock_service_dependencies):
    """Test that zookeeper_url is derived correctly in poll_status."""
    from mindweaver.platform_service.zookeeper.model import ZookeeperPlatformState
    request, session = mock_service_dependencies
    svc = ZookeeperPlatformService(request, session)

    model = ZookeeperPlatform(
        name="test-zk",
        project_id=1,
    )

    mock_state = MagicMock(spec=ZookeeperPlatformState)
    mock_state.active = True

    with patch.object(svc, "platform_state", AsyncMock(return_value=mock_state)), \
         patch.object(svc, "kubeconfig", AsyncMock(return_value="mock-kubeconfig")), \
         patch.object(svc, "_resolve_namespace", AsyncMock(return_value="test-ns")):

        node_ports = []
        cluster_nodes = [{"hostname": "node1", "ipv4": "1.2.3.4", "ipv6": None}]

        async def mock_poll(*args):
            return "online", "Healthy", {}, node_ports, cluster_nodes, "test-zk-client"

        with patch("mindweaver.platform_service.zookeeper.service.asyncio.to_thread", side_effect=mock_poll):
            mock_project = MagicMock()
            mock_project.ingress_domain = None
            svc.project = AsyncMock(return_value=mock_project)

            await svc.poll_status(model)

            # Zookeeper URL should be derived as <service>.<namespace>.svc.cluster.local:2181
            assert mock_state.zookeeper_url == "test-zk-client.test-ns.svc.cluster.local:2181"
