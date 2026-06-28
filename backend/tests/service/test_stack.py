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
                    "images": {
                        "main": {"image": "apache/nifi", "tag": "2.0"}
                    }
                }
            }
        }
    )

    assert stack.get_chart_version_for_component("trino") == "2.0.0"
    assert stack.get_chart_version_for_component("nifi") is None
    assert stack.get_chart_version_for_component("nonexistent") is None


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
                    "chart_version": "9.9.9",
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
