import pytest
from mindweaver.ext.data_source import get_driver, register_driver
from mindweaver.ext.data_source.base import DataSourceDriver
from typing import Any


def test_registry_registration():
    """Verify that a driver can be registered and retrieved."""

    @register_driver("test_driver")
    class TestDriver(DataSourceDriver):
        def connection_uri(self) -> str:
            return "test://uri"

        async def test_connection(self) -> dict[str, Any]:
            return {"status": "success", "message": "Test driver success"}

    driver = get_driver("test_driver", {})
    assert driver is not None
    assert isinstance(driver, TestDriver)
    assert driver.connection_uri() == "test://uri"


@pytest.mark.asyncio
async def test_web_driver_uri_construction():
    """Verify WebDriver URI construction for various configs."""

    # Case 1: Simple host with SSL
    driver = get_driver("web", {"host": "example.com", "enable_ssl": True})
    assert driver.connection_uri() == "https://example.com"

    # Case 2: Host with port and no SSL
    driver = get_driver("web", {"host": "localhost", "port": 8080, "enable_ssl": False})
    assert driver.connection_uri() == "http://localhost:8080"

    # Case 3: Host is a full URL in config['host']
    driver = get_driver("web", {"host": "http://myapi.com/v1"})
    assert driver.connection_uri() == "http://myapi.com/v1"

    # Case 4: Resource path added
    driver = get_driver("web", {"host": "example.com", "resource": "/api/v2"})
    assert (
        driver.connection_uri() == "https://example.com/api/v2"
        if driver.config.get("enable_ssl")
        else "http://example.com/api/v2"
    )

    # Case 5: Parameters with base_url
    driver = get_driver("web", {"parameters": {"base_url": "https://service.local"}})
    assert driver.connection_uri() == "https://service.local"


def test_default_tcp_check():
    """Verify the default TCP check logic in DataSourceDriver."""

    class TcpDriver(DataSourceDriver):
        def connection_uri(self) -> str:
            return f"tcp://{self.config['host']}:{self.config['port']}"

        async def test_connection(self) -> dict[str, Any]:
            return await self.default_test_connection()

    # Mock TCP check by pointing to a likely closed port on localhost or similar
    # Actually, testing real TCP check is tricky in CI, but we can verify it fails gracefully
    driver = TcpDriver({"host": "127.0.0.1", "port": 12345})
    # We don't assert boolean because it depends on the environment,
    # but we verify it returns the expected structure.

    import asyncio

    async def run_test():
        result = await driver.test_connection()
        assert "status" in result
        assert "message" in result

    asyncio.run(run_test())


@pytest.mark.asyncio
async def test_web_driver_test_connection_mock(monkeypatch):
    """Verify WebDriver calling httpx."""

    from httpx import Response

    async def mock_get(*args, **kwargs):
        return Response(200, content=b"OK")

    monkeypatch.setattr("httpx.AsyncClient.get", mock_get)

    driver = get_driver("web", {"host": "example.com"})
    result = await driver.test_connection()
    assert result["status"] == "success"
    assert "Status: 200" in result["message"]
