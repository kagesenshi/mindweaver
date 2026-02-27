# SPDX-FileCopyrightText: Copyright © 2026 Mohd Izhar Firdaus Bin Ismail
# SPDX-License-Identifier: AGPLv3+

from typing import Type, Optional
from ..state import BaseState


class ServiceStateMixin:
    """
    Mixin for services that handle state.
    """

    _state_class: Optional[Type[BaseState]] = None

    @classmethod
    def get_state_class(cls) -> Optional[Type[BaseState]]:
        """Returns the registered state class for this service and its bases."""
        for base in cls.__mro__:
            if (
                "_state_class" in base.__dict__
                and base.__dict__["_state_class"] is not None
            ):
                return base.__dict__["_state_class"]
        return None

    @classmethod
    def with_state(cls):
        """Decorator to register a state class on the service."""

        def decorator(state_cls: Type[BaseState]):
            cls._state_class = state_cls
            return state_cls

        return decorator
