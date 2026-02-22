import pytest
import asyncio
from unittest.mock import MagicMock, patch
from sqlalchemy.engine import URL
import os
import sys

# Add src to sys.path
sys.path.append(os.path.join(os.getcwd(), "backend/src"))

from mindweaver.service.data_source import DataSourceService

@pytest.mark.asyncio
async def test_perform_test_connection_postgresql_uses_thread():
    svc = DataSourceService(None)
    config = {
        "driver": "postgresql",
        "host": "localhost",
        "port": 5432,
        "resource": "mydb",
        "login": "user",
        "password": "pass",
        "parameters": {}
    }

    # Mock get_driver to return None so it falls through to SQLAlchemy logic
    with patch("mindweaver.service.data_source.get_driver", return_value=None), \
         patch("mindweaver.service.data_source.create_engine") as mock_create_engine, \
         patch("asyncio.to_thread", side_effect=asyncio.to_thread) as mock_to_thread:

        mock_engine = MagicMock()
        mock_create_engine.return_value = mock_engine

        result = await svc.perform_test_connection(config)

        assert result["status"] == "success"
        assert "Successfully connected to postgresql" in result["message"]

        # Verify asyncio.to_thread was called
        mock_to_thread.assert_called()

        # Verify create_engine was called (inside the thread)
        mock_create_engine.assert_called()
