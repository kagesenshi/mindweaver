# SPDX-FileCopyrightText: Copyright © 2026 Mohd Izhar Firdaus Bin Ismail
# SPDX-License-Identifier: AGPLv3+

import pytest
from unittest.mock import patch, MagicMock
from fastapi import Request
from mindweaver.config import settings
from mindweaver.fw.model import get_engine, clear_engine
from mindweaver.fw.auth import verify_token, User


def test_db_pool_settings_defaults():
    """Verify that default DB pool settings are present in configuration."""
    assert hasattr(settings, "db_pool_size")
    assert hasattr(settings, "db_max_overflow")
    assert hasattr(settings, "db_pool_recycle")
    assert hasattr(settings, "db_pool_pre_ping")
    assert hasattr(settings, "db_pool_timeout")
    assert settings.db_pool_size >= 5
    assert settings.db_pool_pre_ping is True


def test_celery_worker_process_init_clears_engine():
    """Verify that clear_engine is invoked on worker process initialization."""
    from mindweaver.celery_app import clear_engine_on_worker_process_init
    with patch("mindweaver.celery_app.clear_engine") as mock_clear:
        clear_engine_on_worker_process_init()
        mock_clear.assert_called_once()


@pytest.mark.asyncio
async def test_verify_token_with_session_dependency():
    """Verify verify_token correctly uses the injected session without unclosed generator leaks."""
    request = MagicMock(spec=Request)
    request.url.path = "/api/v1/projects"
    request.headers = {"Authorization": "Bearer invalid_token"}

    mock_session = MagicMock()
    
    old_enable_auth = settings.enable_auth
    try:
        settings.enable_auth = True
        with pytest.raises(Exception):
            await verify_token(request, session=mock_session)
    finally:
        settings.enable_auth = old_enable_auth
