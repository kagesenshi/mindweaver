# SPDX-FileCopyrightText: Copyright © 2026 Mohd Izhar Firdaus Bin Ismail
# SPDX-License-Identifier: AGPLv3+

import pytest
from unittest.mock import MagicMock, patch
from fastapi import Request
from sqlmodel import Session
from datetime import datetime

from mindweaver.platform_service.pgsql import (
    PgSqlPlatform,
    PgSqlPlatformService,
)
from mindweaver.platform_service.pgsql.actions import PgSqlBackupAction

from mindweaver.platform_service.base import PlatformStateBase


class MockState:
    def __init__(self, active=True):
        self.active = active


@pytest.mark.asyncio
async def test_pgsql_backup_action_available():
    model = PgSqlPlatform(id=1, name="test-db")
    svc = MagicMock(spec=PgSqlPlatformService)

    action = PgSqlBackupAction(model, svc)

    # Test case: state is active
    svc.platform_state.return_value = MockState(active=True)
    assert await action.available() is True

    # Test case: state is inactive
    svc.platform_state.return_value = MockState(active=False)
    assert await action.available() is False

    # Test case: state doesn't exist
    svc.platform_state.return_value = None
    assert await action.available() is False


@pytest.mark.asyncio
async def test_pgsql_backup_action_call():
    model = PgSqlPlatform(id=1, name="test-db")
    svc = MagicMock(spec=PgSqlPlatformService)
    svc.kubeconfig.return_value = "fake-kubeconfig"
    svc._resolve_namespace.return_value = "test-namespace"

    action = PgSqlBackupAction(model, svc)

    with patch(
        "mindweaver.platform_service.pgsql.actions.config"
    ) as mock_config, patch(
        "mindweaver.platform_service.pgsql.actions.client"
    ) as mock_client, patch(
        "mindweaver.platform_service.pgsql.actions.tempfile.NamedTemporaryFile"
    ) as mock_tempfile:

        # Setup mocks
        mock_temp = MagicMock()
        mock_temp.__enter__.return_value.name = "/tmp/fake-kubeconfig"
        mock_tempfile.return_value = mock_temp

        mock_custom_api = MagicMock()
        mock_client.CustomObjectsApi.return_value = mock_custom_api

        # Execute action
        result = await action()

        # Verify
        assert result["status"] == "success"
        assert result["backup_name"].startswith("backup-")

        mock_custom_api.create_namespaced_custom_object.assert_called_once()
        args, kwargs = mock_custom_api.create_namespaced_custom_object.call_args

        assert kwargs["group"] == "postgresql.cnpg.io"
        assert kwargs["version"] == "v1"
        assert kwargs["namespace"] == "test-namespace"
        assert kwargs["plural"] == "backups"

        body = kwargs["body"]
        assert body["kind"] == "Backup"
        assert body["spec"]["cluster"]["name"] == "test-db"
        assert body["spec"]["method"] == "barmanObjectStore"
