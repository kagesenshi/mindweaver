from typing import Dict, Type, Optional, Any
from .base import DataSourceDriver


class DriverRegistry:
    """
    Registry for data source drivers.
    """

    _drivers: Dict[str, Dict[str, Any]] = {}

    @classmethod
    def register(
        cls,
        name: str,
        driver_cls: Type[DataSourceDriver],
        title: Optional[str] = None,
        description: Optional[str] = None,
    ):
        """
        Register a new driver class.
        """
        cls._drivers[name.lower()] = {
            "class": driver_cls,
            "title": title or name.capitalize(),
            "description": description or "",
        }

    @classmethod
    def get_driver(
        cls, name: str, config: dict[str, Any]
    ) -> Optional[DataSourceDriver]:
        """
        Get an instance of a registered driver.
        """
        driver_info = cls._drivers.get(name.lower())
        if driver_info:
            return driver_info["class"](config)
        return None

    @classmethod
    def list_drivers(cls) -> list[str]:
        """
        List all registered driver names.
        """
        return list(cls._drivers.keys())

    @classmethod
    def get_driver_options(cls) -> list[dict[str, str]]:
        """
        Get driver options for UI select widget.
        """
        return [
            {"label": info["title"], "value": name}
            for name, info in cls._drivers.items()
        ]


def register_driver(
    name: str, title: Optional[str] = None, description: Optional[str] = None
):
    """
    Decorator to register a driver class.
    """

    def decorator(cls: Type[DataSourceDriver]):
        DriverRegistry.register(name, cls, title=title, description=description)
        return cls

    return decorator


def get_driver(name: str, config: dict[str, Any]) -> Optional[DataSourceDriver]:
    """
    Convenience function to get a driver instance.
    """
    return DriverRegistry.get_driver(name, config)


def get_driver_options() -> list[dict[str, str]]:
    """
    Get driver options for UI select widget.
    """
    return DriverRegistry.get_driver_options()


# Import drivers here to trigger registration
from . import web  # noqa: F401
