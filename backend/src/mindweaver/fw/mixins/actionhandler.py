# SPDX-FileCopyrightText: Copyright © 2026 Mohd Izhar Firdaus Bin Ismail
# SPDX-License-Identifier: AGPLv3+

from typing import Dict, List, Any, Type
from ..action import BaseAction


class ActionHandlerMixin:
    """
    Mixin for services that handle custom actions.
    """

    _actions: Dict[str, Type[BaseAction]] = {}

    @classmethod
    def get_actions(cls) -> Dict[str, Type[BaseAction]]:
        """Returns all registered actions for this class and its bases."""
        actions = {}
        for base in reversed(cls.__mro__):
            if "_actions" in base.__dict__ and isinstance(
                base.__dict__["_actions"], dict
            ):
                actions.update(base.__dict__["_actions"])
        return actions

    @classmethod
    def register_action(cls, name: str):
        """Decorator to register a new action on the service."""

        def decorator(action_cls):
            if "_actions" not in cls.__dict__:
                cls._actions = {}
            if name in cls._actions:
                raise ValueError(
                    f"Action '{name}' is already registered on {cls.__name__}"
                )
            cls._actions[name] = action_cls
            return action_cls

        return decorator
