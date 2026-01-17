from mindweaver.ext.data_source import (
    get_driver_options,
    DriverRegistry,
    DataSourceDriver,
    register_driver,
)
import pytest


def test_get_driver_options():
    options = get_driver_options()
    # At least 'web' should be there
    assert any(opt["value"] == "web" for opt in options)
    web_opt = next(opt for opt in options if opt["value"] == "web")
    assert web_opt["label"] == "Web / API"


def test_register_custom_driver():
    @register_driver("test_driver", title="Test Driver", description="A test driver")
    class TestDriver(DataSourceDriver):
        async def test_connection(self):
            return {"status": "success", "message": "ok"}

        def connection_uri(self):
            return "test://"

    options = get_driver_options()
    assert any(opt["value"] == "test_driver" for opt in options)
    test_opt = next(opt for opt in options if opt["value"] == "test_driver")
    assert test_opt["label"] == "Test Driver"

    # Cleanup (manual since it's a global registry for now)
    if "test_driver" in DriverRegistry._drivers:
        del DriverRegistry._drivers["test_driver"]
