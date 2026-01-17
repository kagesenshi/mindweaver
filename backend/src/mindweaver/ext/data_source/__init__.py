from typing import Dict, Type, Optional, Any
from .base import DataSourceDriver


class DriverRegistry:
    """
    Registry for data source drivers.
    """

    _drivers: Dict[str, Type[DataSourceDriver]] = {}

    @classmethod
    def register(cls, name: str, driver_cls: Type[DataSourceDriver]):
        """
        Register a new driver class.
        """
        cls._drivers[name.lower()] = driver_cls

    @classmethod
    def get_driver(
        cls, name: str, config: dict[str, Any]
    ) -> Optional[DataSourceDriver]:
        """
        Get an instance of a registered driver.
        """
        driver_cls = cls._drivers.get(name.lower())
        if driver_cls:
            return driver_cls(config)
        return None

    @classmethod
    def list_drivers(cls) -> list[str]:
        """
        List all registered driver names.
        """
        return list(cls._drivers.keys())


def register_driver(name: str):
    """
    Decorator to register a driver class.
    """

    def decorator(cls: Type[DataSourceDriver]):
        DriverRegistry.register(name, cls)
        return cls

    return decorator


def get_driver(name: str, config: dict[str, Any]) -> Optional[DataSourceDriver]:
    """
    Convenience function to get a driver instance.
    """
    return DriverRegistry.get_driver(name, config)


# Import drivers here to trigger registration
from . import web  # noqa: F401
