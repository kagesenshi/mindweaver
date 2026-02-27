# SPDX-FileCopyrightText: Copyright © 2026 Mohd Izhar Firdaus Bin Ismail
# SPDX-License-Identifier: AGPLv3+

from typing import Dict, List, Any


class CustomViewMixin:
    """
    Mixin for services that handle custom views.
    """

    _custom_views: List[Dict[str, Any]] = []

    @classmethod
    def get_custom_views(cls) -> List[Dict[str, Any]]:
        """Returns all registered custom views for this class and its bases."""
        views = []
        for base in reversed(cls.__mro__):
            if "_custom_views" in base.__dict__ and isinstance(
                base.__dict__["_custom_views"], list
            ):
                views.extend(base.__dict__["_custom_views"])
        return views

    @classmethod
    def service_view(cls, method: str, path: str, **kwargs):
        """Decorator to register a new service level custom view on the service."""

        def decorator(cls_func):
            if "_custom_views" not in cls.__dict__:
                cls._custom_views = []
            cls._custom_views.append(
                {
                    "type": "service",
                    "method": method,
                    "path": path,
                    "func": cls_func,
                    "kwargs": kwargs,
                }
            )
            return cls_func

        return decorator

    @classmethod
    def model_view(cls, method: str, path: str, **kwargs):
        """Decorator to register a new model level custom view on the service."""

        def decorator(cls_func):
            if "_custom_views" not in cls.__dict__:
                cls._custom_views = []
            cls._custom_views.append(
                {
                    "type": "model",
                    "method": method,
                    "path": path,
                    "func": cls_func,
                    "kwargs": kwargs,
                }
            )
            return cls_func

        return decorator
