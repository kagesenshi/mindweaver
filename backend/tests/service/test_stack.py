# SPDX-FileCopyrightText: Copyright © 2026 Mohd Izhar Firdaus Bin Ismail
# SPDX-License-Identifier: AGPLv3+

import pytest
from unittest.mock import AsyncMock, MagicMock
from sqlmodel import select
from fastapi import Request
from mindweaver.fw.model import AsyncSession

from mindweaver.service.stack.model import Stack
from mindweaver.platform_service.base import PlatformService
from mindweaver.platform_service.trino.service import TrinoPlatformService
from mindweaver.platform_service.trino.model import TrinoPlatform
from mindweaver.service.project.model import Project


@pytest.fixture
def mock_service_dependencies():
    request = MagicMock(spec=Request)
    session = MagicMock(spec=AsyncSession)
    session.exec = AsyncMock()
    return request, session


def test_stack_chart_version_resolution():
    """Test get_chart_version_for_component returns correct values from Stack configuration."""
    stack = Stack(
        name="test-stack",
        version="1.0.0",
        configuration={
            "components": {
                "trino": {
                    "chart_version": "2.0.0",
                    "images": {
                        "main": {"image": "trinodb/trino", "tag": "400"}
                    }
                },
                "nifi": {
                    "charts": {
                        "main": {
                            "repo": "ghcr.io/konpyutaika/helm-charts",
                            "chart": "nifi-cluster",
                            "version": "1.17.0"
                        }
                    }
                }
            }
        }
    )

    assert stack.get_chart_version_for_component("trino") == "2.0.0"
    assert stack.get_chart_version_for_component("nifi") == "1.17.0"
    assert stack.get_chart_version_for_component("nonexistent") is None


def test_stack_chart_resolution():
    """Test get_chart_for_component returns correct tuple of (repo, chart, version)."""
    stack = Stack(
        name="test-stack",
        version="1.0.0",
        configuration={
            "components": {
                "nifi": {
                    "charts": {
                        "main": {
                            "repo": "ghcr.io/konpyutaika/helm-charts",
                            "chart": "nifi-cluster",
                            "version": "1.17.0"
                        },
                        "custom": {
                            "repo": "my-repo",
                            "chart": "my-chart",
                            "version": "2.0.0"
                        }
                    }
                }
            }
        }
    )

    assert stack.get_chart_for_component("nifi", "main") == ("ghcr.io/konpyutaika/helm-charts", "nifi-cluster", "1.17.0")
    assert stack.get_chart_for_component("nifi", "custom") == ("my-repo", "my-chart", "2.0.0")
    assert stack.get_chart_for_component("nifi", "nonexistent") == (None, None, None)
    assert stack.get_chart_for_component("nonexistent") == (None, None, None)


@pytest.mark.asyncio
async def test_resolve_chart_version(mock_service_dependencies):
    """Test resolve_chart_version fallback behavior and stack resolution."""
    request, _ = mock_service_dependencies
    
    class DummySession:
        pass
        
    session = DummySession()
    svc = TrinoPlatformService(request, session)

    # 1. Test fallback when no stack is linked
    model = TrinoPlatform(
        name="trino-test",
        title="Trino Test",
        project_id=1,
    )
    project = Project(id=1, name="proj", title="Proj", stack_id=None)
    svc.project = AsyncMock(return_value=project)

    resolved_version = await svc.resolve_chart_version(model, "trino", "1.41.0")
    assert resolved_version == "1.41.0"

    # 2. Test resolution when stack is linked
    stack = Stack(
        id=5,
        name="my-stack",
        version="0.1.0",
        configuration={
            "components": {
                "trino": {
                    "charts": {
                        "main": {
                            "repo": "https://trinodb.github.io/charts",
                            "chart": "trino",
                            "version": "9.9.9",
                        }
                    }
                }
            }
        }
    )
    project.stack_id = 5

    # Mock session.exec(select(Stack)...)
    mock_result = MagicMock()
    mock_result.one_or_none.return_value = stack
    session.exec = AsyncMock(return_value=mock_result)

    resolved_version = await svc.resolve_chart_version(model, "trino", "1.41.0")
    assert resolved_version == "9.9.9"

    # 3. Test resolve_chart directly
    repo, chart, version = await svc.resolve_chart(
        model, "trino", "main", "https://default-repo", "default-chart", "1.0.0"
    )
    assert repo == "https://trinodb.github.io/charts"
    assert chart == "trino"
    assert version == "9.9.9"


@pytest.mark.asyncio
async def test_resolve_integration_version(mock_service_dependencies):
    """Test resolve_integration_version behaves correctly for cluster integrations."""
    from mindweaver.service.k8s_cluster.actions import InstallArgoCDAction
    from mindweaver.service.k8s_cluster.model import K8sCluster
    from mindweaver.service.k8s_cluster.service import K8sClusterService
    
    request, _ = mock_service_dependencies
    
    class DummySession:
        pass
        
    session = DummySession()
    cluster = K8sCluster(id=1, name="test-cluster")
    svc = K8sClusterService(request, session)
    action = InstallArgoCDAction(cluster, svc)
    action.session = session

    # 1. Test fallback when no stack exists
    mock_result = MagicMock()
    mock_result.first.return_value = None
    session.exec = AsyncMock(return_value=mock_result)
    
    version = await action.resolve_integration_version("cert-manager", "v1.20.0")
    assert version == "v1.20.0"

    # 2. Test resolution from the project stack
    stack = Stack(
        id=5,
        name="my-stack",
        version="0.1.0",
        configuration={
            "components": {
                "cert-manager": {
                    "charts": {
                        "main": {
                            "repo": "https://charts.jetstack.io",
                            "chart": "cert-manager",
                            "version": "v1.99.0",
                        }
                    }
                }
            }
        }
    )
    project = Project(id=1, name="proj", title="Proj", stack_id=5)
    
    mock_result_proj = MagicMock()
    mock_result_proj.first.return_value = project
    
    mock_result_stack = MagicMock()
    mock_result_stack.one_or_none.return_value = stack
    
    session.exec = AsyncMock(side_effect=[mock_result_proj, mock_result_stack])
    
    version = await action.resolve_integration_version("cert-manager", "v1.20.0")
    assert version == "v1.99.0"

