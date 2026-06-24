# SPDX-FileCopyrightText: Copyright © 2026 Mohd Izhar Firdaus Bin Ismail
# SPDX-License-Identifier: AGPLv3+

import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from fastapi import Request
from pydantic import ValidationError
from mindweaver.platform_service.nifi import NifiPlatform, NifiPlatformService
from mindweaver.fw.model import AsyncSession

@pytest.fixture
def mock_service_dependencies():
    request = MagicMock(spec=Request)
    session = MagicMock(spec=AsyncSession)
    session.exec = AsyncMock()
    session.flush = AsyncMock()
    return request, session

def test_nifi_resource_defaults():
    """Test default values for NiFi resource limits and replicas."""
    model = NifiPlatform(name="test-nifi", title="Test NiFi", project_id=1)
    assert model.replica_count == 1
    assert model.storage_size == "10Gi"
    assert model.cpu_request == 0.5
    assert model.cpu_limit == 2.0
    assert model.mem_request == 2.0
    assert model.mem_limit == 4.0
    assert model.chart_version == "1.17.0"
    assert model.image_tag == "2.9.0"

def test_nifi_cpu_validation():
    """Test that CPU request cannot exceed CPU limit."""
    with pytest.raises(ValidationError) as excinfo:
        NifiPlatform.model_validate(
            {
                "name": "test-nifi",
                "title": "Test NiFi",
                "project_id": 1,
                "cpu_request": 4.0,
                "cpu_limit": 2.0,
            }
        )
    assert "CPU request cannot be greater than CPU limit" in str(excinfo.value)

def test_nifi_mem_validation():
    """Test that memory request cannot exceed memory limit."""
    with pytest.raises(ValidationError) as excinfo:
        NifiPlatform.model_validate(
            {
                "name": "test-nifi",
                "title": "Test NiFi",
                "project_id": 1,
                "mem_request": 8.0,
                "mem_limit": 4.0,
            }
        )
    assert "Memory request cannot be greater than Memory limit" in str(excinfo.value)

def test_nifi_version_validation():
    """Test that only NiFi 2.x versions are allowed."""
    # Valid NiFi 2.x versions
    for valid_tag in ["2.0.0", "2.9.0", "2.10.0-RC1"]:
        model = NifiPlatform.model_validate(
            {
                "name": "test-nifi",
                "title": "Test NiFi",
                "project_id": 1,
                "image_tag": valid_tag,
            }
        )
        assert model.image_tag == valid_tag

    # Invalid NiFi versions (1.x, etc.)
    for invalid_tag in ["1.20.0", "1.19.1", "3.0.0"]:
        with pytest.raises(ValidationError) as excinfo:
            NifiPlatform.model_validate(
                {
                    "name": "test-nifi",
                    "title": "Test NiFi",
                    "project_id": 1,
                    "image_tag": invalid_tag,
                }
            )
        assert "Only NiFi 2.x series is supported" in str(excinfo.value)

@pytest.mark.asyncio
async def test_nifi_template_vars(mock_service_dependencies):
    """Test that template_vars returns expected template variable mappings."""
    request, session = mock_service_dependencies
    svc = NifiPlatformService(request, session)

    model = NifiPlatform(
        name="test-nifi",
        project_id=1,
        replica_count=3,
        storage_size="20Gi",
    )

    svc._resolve_namespace = AsyncMock(return_value="test-ns")
    svc.project = AsyncMock(return_value=MagicMock(ingress_domain=None))

    vars = await svc.template_vars(model)

    assert vars["name"] == "test-nifi"
    assert vars["namespace"] == "test-ns"
    assert vars["replica_count"] == 3
    assert vars["storage_size"] == "20Gi"

@pytest.mark.asyncio
async def test_nifi_render_manifests(mock_service_dependencies):
    """Test that the ArgoCD Application manifests render correctly."""
    request, session = mock_service_dependencies
    svc = NifiPlatformService(request, session)

    model = NifiPlatform(
        name="test-nifi",
        project_id=1,
        replica_count=3,
        storage_size="20Gi",
    )

    svc._resolve_namespace = AsyncMock(return_value="test-ns")
    svc.project = AsyncMock(return_value=MagicMock(ingress_domain=None))

    manifests = await svc.render_manifests(model)

    assert "name: test-nifi" in manifests
    assert "chart: nifi-cluster" in manifests
    assert "repoURL: ghcr.io/konpyutaika/helm-charts" in manifests
    assert "storage: \"20Gi\"" in manifests
    assert "namespace: test-ns" in manifests

@pytest.mark.asyncio
async def test_nifi_poll_status(mock_service_dependencies):
    """Test that nifi_uri is derived correctly in poll_status."""
    from mindweaver.platform_service.nifi.model import NifiPlatformState
    request, session = mock_service_dependencies
    svc = NifiPlatformService(request, session)

    model = NifiPlatform(
        name="test-nifi",
        project_id=1,
    )

    mock_state = MagicMock(spec=NifiPlatformState)
    mock_state.active = True

    with patch.object(svc, "platform_state", AsyncMock(return_value=mock_state)), \
         patch.object(svc, "kubeconfig", AsyncMock(return_value="mock-kubeconfig")), \
         patch.object(svc, "_resolve_namespace", AsyncMock(return_value="test-ns")):

        node_ports = []
        cluster_nodes = [{"hostname": "node1", "ipv4": "1.2.3.4", "ipv6": None}]

        async def mock_poll(*args):
            return "online", "Healthy", {}, node_ports, cluster_nodes

        with patch("mindweaver.platform_service.nifi.service.asyncio.to_thread", side_effect=mock_poll):
            mock_project = MagicMock()
            mock_project.ingress_domain = "example.com"
            svc.project = AsyncMock(return_value=mock_project)

            await svc.poll_status(model)

            # NiFi URL should be derived using ingress domain
            assert mock_state.nifi_uri == "https://test-nifi.example.com"
