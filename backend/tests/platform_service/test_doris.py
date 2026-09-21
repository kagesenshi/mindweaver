# SPDX-FileCopyrightText: Copyright © 2026 Mohd Izhar Firdaus Bin Ismail
# SPDX-License-Identifier: AGPLv3+

import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from fastapi import Request
from pydantic import ValidationError
from mindweaver.platform_service.doris import DorisPlatform, DorisPlatformService, DorisPlatformState
from mindweaver.platform_service.doris.poller import DorisPoller
from mindweaver.fw.model import AsyncSession


@pytest.fixture
def mock_service_dependencies():
    """Provides mock request and session objects for service tests."""
    request = MagicMock(spec=Request)
    session = MagicMock(spec=AsyncSession)
    mock_exec_result = MagicMock()
    mock_exec_result.all.return_value = []
    mock_exec_result.first.return_value = None
    session.exec = AsyncMock(return_value=mock_exec_result)
    session.flush = AsyncMock()
    session.add = MagicMock()
    return request, session


def test_doris_resource_defaults():
    """Test default values for Doris platform model."""
    model = DorisPlatform(name="test-doris", title="Test Doris", project_id=1)
    assert model.fe_replicas == 3
    assert model.be_replicas == 3
    assert model.fe_storage_size == "10Gi"
    assert model.be_storage_size == "50Gi"
    assert model.fe_cpu_request == 0.5
    assert model.fe_cpu_limit == 2.0
    assert model.fe_mem_request == 2.0
    assert model.fe_mem_limit == 4.0
    assert model.be_cpu_request == 0.5
    assert model.be_cpu_limit == 2.0
    assert model.be_mem_request == 2.0
    assert model.be_mem_limit == 4.0
    assert model.admin_password is not None
    assert len(model.admin_password) >= 16


def test_doris_cpu_validation():
    """Test that FE and BE CPU request cannot exceed limits."""
    # Invalid FE CPU
    with pytest.raises(ValidationError) as excinfo:
        DorisPlatform.model_validate(
            {
                "name": "test-doris",
                "title": "Test Doris",
                "project_id": 1,
                "fe_cpu_request": 4.0,
                "fe_cpu_limit": 2.0,
            }
        )
    assert "FE CPU request cannot be greater than FE CPU limit" in str(excinfo.value)

    # Invalid BE CPU
    with pytest.raises(ValidationError) as excinfo:
        DorisPlatform.model_validate(
            {
                "name": "test-doris",
                "title": "Test Doris",
                "project_id": 1,
                "be_cpu_request": 4.0,
                "be_cpu_limit": 2.0,
            }
        )
    assert "BE CPU request cannot be greater than BE CPU limit" in str(excinfo.value)


def test_doris_mem_validation():
    """Test that FE and BE Memory request cannot exceed limits."""
    # Invalid FE Memory
    with pytest.raises(ValidationError) as excinfo:
        DorisPlatform.model_validate(
            {
                "name": "test-doris",
                "title": "Test Doris",
                "project_id": 1,
                "fe_mem_request": 8.0,
                "fe_mem_limit": 4.0,
            }
        )
    assert "FE Memory request cannot be greater than FE Memory limit" in str(excinfo.value)

    # Invalid BE Memory
    with pytest.raises(ValidationError) as excinfo:
        DorisPlatform.model_validate(
            {
                "name": "test-doris",
                "title": "Test Doris",
                "project_id": 1,
                "be_mem_request": 8.0,
                "be_mem_limit": 4.0,
            }
        )
    assert "BE Memory request cannot be greater than BE Memory limit" in str(excinfo.value)


def test_doris_replica_count_validation():
    """Test that FE and BE replica counts are validated properly."""
    # FE replicas must be odd positive numbers
    for valid_fe in [1, 3, 5, 7]:
        model = DorisPlatform.model_validate(
            {
                "name": "test-doris",
                "title": "Test Doris",
                "project_id": 1,
                "fe_replicas": valid_fe,
            }
        )
        assert model.fe_replicas == valid_fe

    for invalid_fe in [0, 2, 4, -1]:
        with pytest.raises(ValidationError) as excinfo:
            DorisPlatform.model_validate(
                {
                    "name": "test-doris",
                    "title": "Test Doris",
                    "project_id": 1,
                    "fe_replicas": invalid_fe,
                }
            )
        assert "FE replicas must be an odd positive number" in str(excinfo.value)

    # BE replicas must be positive
    for valid_be in [1, 2, 3, 5]:
        model = DorisPlatform.model_validate(
            {
                "name": "test-doris",
                "title": "Test Doris",
                "project_id": 1,
                "be_replicas": valid_be,
            }
        )
        assert model.be_replicas == valid_be

    for invalid_be in [0, -1]:
        with pytest.raises(ValidationError) as excinfo:
            DorisPlatform.model_validate(
                {
                    "name": "test-doris",
                    "title": "Test Doris",
                    "project_id": 1,
                    "be_replicas": invalid_be,
                }
            )
        assert "BE replicas must be at least 1" in str(excinfo.value)


@pytest.mark.asyncio
async def test_doris_template_vars(mock_service_dependencies):
    """Test that template_vars generates expected template values."""
    request, session = mock_service_dependencies
    svc = DorisPlatformService(request, session)

    model = DorisPlatform(
        name="doris-cluster",
        title="Doris Analytics",
        project_id=1,
        fe_replicas=3,
        be_replicas=3,
        fe_storage_size="10Gi",
        be_storage_size="50Gi",
    )

    svc._resolve_namespace = AsyncMock(return_value="test-ns")
    mock_project = MagicMock(
        name="default",
        title="Default Project",
        ingress_domain="apps.example.com",
        stack_id=None,
    )
    svc.project = AsyncMock(return_value=mock_project)

    vars_dict = await svc.template_vars(model)

    assert vars_dict["name"] == "doris-cluster"
    assert vars_dict["fe_replicas"] == 3
    assert vars_dict["be_replicas"] == 3
    assert vars_dict["fe_storage_size"] == "10Gi"
    assert vars_dict["be_storage_size"] == "50Gi"
    assert vars_dict["fe_image"] == "selectdb/doris.fe-ubuntu"
    assert vars_dict["fe_image_tag"] == "2.1.8"
    assert vars_dict["be_image"] == "selectdb/doris.be-ubuntu"
    assert vars_dict["be_image_tag"] == "2.1.8"
    assert vars_dict["ingress_domain"] == "apps.example.com"
    assert vars_dict["namespace"] == "test-ns"


@pytest.mark.asyncio
async def test_doris_render_manifests(mock_service_dependencies):
    """Test rendering Kubernetes manifests from templates."""
    request, session = mock_service_dependencies
    svc = DorisPlatformService(request, session)

    model = DorisPlatform(
        name="doris-main",
        title="Doris Main",
        project_id=1,
    )

    svc._resolve_namespace = AsyncMock(return_value="proj1")
    mock_project = MagicMock(
        name="proj1",
        title="Project One",
        ingress_domain="apps.example.com",
        stack_id=None,
    )
    svc.project = AsyncMock(return_value=mock_project)

    manifests = await svc.render_manifests(model)
    assert "kind: Application" in manifests
    assert "kind: Secret" in manifests
    assert "kind: HTTPRoute" in manifests
    assert "doris-main" in manifests


@pytest.mark.asyncio
async def test_doris_poller(mock_service_dependencies):
    """Test DorisPoller updating state from cluster info."""
    request, session = mock_service_dependencies
    svc = DorisPlatformService(request, session)

    model = DorisPlatform(
        id=10,
        name="doris-test",
        title="Doris Test",
        project_id=1,
    )

    state = DorisPlatformState(platform_id=10, active=True)
    svc.platform_state = AsyncMock(return_value=state)
    svc.kubeconfig = AsyncMock(return_value=None)
    svc._resolve_namespace = AsyncMock(return_value="default")
    svc.project = AsyncMock(return_value=MagicMock(ingress_domain="example.com"))

    with patch("asyncio.to_thread") as mock_thread:
        mock_thread.return_value = (
            "online",
            "Sync: Synced, Health: Healthy | Pods: FE 3/3, BE 3/3",
            {"sync": {"status": "Synced"}, "health": {"status": "Healthy"}},
            [
                {"name": "doris-test-fe-service", "port": 9030, "node_port": 30930, "protocol": "mysql"},
                {"name": "doris-test-fe-service", "port": 8030, "node_port": 30830, "protocol": "http"},
            ],
            [{"hostname": "node1", "ipv4": "192.168.1.100", "ipv6": None}],
        )

        poller = DorisPoller(svc, model)
        await poller.poll()

        assert state.status == "online"
        assert state.query_uri.startswith("mysql://root:")
        assert "192.168.1.100:30930" in state.query_uri
        assert state.fe_http_uri == "https://doris-test.example.com"
