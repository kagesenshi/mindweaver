# SPDX-FileCopyrightText: Copyright © 2026 Mohd Izhar Firdaus Bin Ismail
# SPDX-License-Identifier: AGPLv3+

import inspect
import graphlib
from typing import TypeVar, Any
from sqlmodel import SQLModel
from .model import NamedBase

T = TypeVar("T", bound=NamedBase)
S = TypeVar("S", bound=SQLModel)


def before_create(func=None, *, before=None, after=None):
    """
    Decorator for hooks to be executed before creating a record.
    """

    def decorator(f):
        sig = inspect.signature(f)
        if len(sig.parameters) != 2:
            raise TypeError(
                f"before_create hook must accept 2 arguments (self, data), got {len(sig.parameters)}"
            )
        f._is_before_create_hook = True
        f._hook_before = [before] if isinstance(before, str) else (before or [])
        f._hook_after = [after] if isinstance(after, str) else (after or [])
        return f

    if func:
        return decorator(func)
    return decorator


def after_create(func=None, *, before=None, after=None):
    """
    Decorator for hooks to be executed after creating a record.
    """

    def decorator(f):
        sig = inspect.signature(f)
        if len(sig.parameters) != 2:
            raise TypeError(
                f"after_create hook must accept 2 arguments (self, model), got {len(sig.parameters)}"
            )
        f._is_after_create_hook = True
        f._hook_before = [before] if isinstance(before, str) else (before or [])
        f._hook_after = [after] if isinstance(after, str) else (after or [])
        return f

    if func:
        return decorator(func)
    return decorator


def before_update(func=None, *, before=None, after=None):
    """
    Decorator for hooks to be executed before updating a record.
    """

    def decorator(f):
        sig = inspect.signature(f)
        if len(sig.parameters) != 3:
            raise TypeError(
                f"before_update hook must accept 3 arguments (self, model, data), got {len(sig.parameters)}"
            )
        f._is_before_update_hook = True
        f._hook_before = [before] if isinstance(before, str) else (before or [])
        f._hook_after = [after] if isinstance(after, str) else (after or [])
        return f

    if func:
        return decorator(func)
    return decorator


def after_update(func=None, *, before=None, after=None):
    """
    Decorator for hooks to be executed after updating a record.
    """

    def decorator(f):
        sig = inspect.signature(f)
        if len(sig.parameters) != 2:
            raise TypeError(
                f"after_update hook must accept 2 arguments (self, model), got {len(sig.parameters)}"
            )
        f._is_after_update_hook = True
        f._hook_before = [before] if isinstance(before, str) else (before or [])
        f._hook_after = [after] if isinstance(after, str) else (after or [])
        return f

    if func:
        return decorator(func)
    return decorator


def before_delete(func=None, *, before=None, after=None):
    """
    Decorator for hooks to be executed before deleting a record.
    """

    def decorator(f):
        sig = inspect.signature(f)
        if len(sig.parameters) != 2:
            raise TypeError(
                f"before_delete hook must accept 2 arguments (self, model), got {len(sig.parameters)}"
            )
        f._is_before_delete_hook = True
        f._hook_before = [before] if isinstance(before, str) else (before or [])
        f._hook_after = [after] if isinstance(after, str) else (after or [])
        return f

    if func:
        return decorator(func)
    return decorator


def after_delete(func=None, *, before=None, after=None):
    """
    Decorator for hooks to be executed after deleting a record.
    """

    def decorator(f):
        sig = inspect.signature(f)
        if len(sig.parameters) != 2:
            raise TypeError(
                f"after_delete hook must accept 2 arguments (self, model), got {len(sig.parameters)}"
            )
        f._is_after_delete_hook = True
        f._hook_before = [before] if isinstance(before, str) else (before or [])
        f._hook_after = [after] if isinstance(after, str) else (after or [])
        return f

    if func:
        return decorator(func)
    return decorator


def _sort_hooks(hooks: list[Any]) -> list[Any]:
    if not hooks:
        return []

    graph = {h.__name__: set() for h in hooks}
    name_to_hook = {h.__name__: h for h in hooks}

    for hook in hooks:
        # Handle 'after' dependencies: hook depends on other (other -> hook)
        for other_name in hook._hook_after:
            if other_name in graph:
                graph[hook.__name__].add(other_name)

        # Handle 'before' dependencies: other depends on hook (hook -> other)
        for other_name in hook._hook_before:
            if other_name in graph:
                graph[other_name].add(hook.__name__)

    ts = graphlib.TopologicalSorter(graph)
    try:
        sorted_names = list(ts.static_order())
    except graphlib.CycleError as e:
        raise ValueError(f"Circular dependency detected in hooks: {e.args[1]}")

    return [name_to_hook[name] for name in sorted_names]
