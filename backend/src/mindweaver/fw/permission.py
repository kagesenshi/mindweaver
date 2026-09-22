# SPDX-FileCopyrightText: Copyright © 2026 Mohd Izhar Firdaus Bin Ismail
# SPDX-License-Identifier: AGPLv3+

import asyncio
import inspect
from typing import Any, Callable, Optional, Type
from fastapi import Depends, HTTPException, Request, params
from sqlmodel.ext.asyncio.session import AsyncSession as SQLModelAsyncSession
from mindweaver.config import settings
from mindweaver.fw.model import AsyncSession, Base, get_engine
from mindweaver.fw.auth import User, get_current_user


_NAME_TO_PERMISSION: dict[str, type["All"]] = {}


class All:
    """Root permission class that all permissions inherit from."""
    name: str = "all"

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        perm_name = getattr(cls, "name", None)
        if perm_name:
            _NAME_TO_PERMISSION[perm_name.lower()] = cls

    @classmethod
    def get_name(cls) -> str:
        """Return the lowercase name of the permission."""
        return getattr(cls, "name", cls.__name__.lower())

    @classmethod
    def check_context(
        cls,
        user: Optional[User] = None,
        context: Optional[Base] = None,
        request: Optional[Request] = None,
    ) -> bool:
        """
        Check if the permission is allowed for the given context (model object).
        Default returns True. Subclasses can override to implement object-level rules.
        """
        return True


_NAME_TO_PERMISSION["all"] = All


class Permission(All):
    """Base class for all specific permissions."""
    name: str = "permission"


class Read(Permission):
    """Base permission for read-only actions."""
    name: str = "read"


class List(Read):
    """Permission to list resources."""
    name: str = "list"


class View(Read):
    """Permission to view a specific resource."""
    name: str = "view"


class Write(Permission):
    """Base permission for mutating actions."""
    name: str = "write"


class Create(Write):
    """Permission to create a new resource."""
    name: str = "create"


class Update(Write):
    """Permission to update an existing resource."""
    name: str = "update"


class Delete(Write):
    """Permission to delete a resource."""
    name: str = "delete"


class Execute(Permission):
    """Permission to execute platform actions or custom tasks."""
    name: str = "execute"


# Aliases
Admin = All
_NAME_TO_PERMISSION["admin"] = Admin


def _eval_context_check(
    perm: type[All] | All,
    user: Optional[User] = None,
    context: Optional[Base] = None,
    request: Optional[Request] = None,
) -> bool:
    """
    Safely evaluate check_context or check_permission on a permission class or instance.
    """
    for method_name in ("check_context", "check_permission"):
        method = getattr(perm, method_name, None)
        if method and callable(method):
            try:
                sig = inspect.signature(method)
                kwargs = {}
                if "user" in sig.parameters:
                    kwargs["user"] = user
                if "context" in sig.parameters:
                    kwargs["context"] = context
                if "request" in sig.parameters:
                    kwargs["request"] = request
                if kwargs:
                    res = method(**kwargs)
                else:
                    res = method(user, context=context, request=request)
            except TypeError:
                try:
                    res = method(user, context, request)
                except TypeError:
                    try:
                        res = method(user, context)
                    except TypeError:
                        res = method(user)
            if not res:
                return False
    return True


def _check_single_permission(
    granted: type[All] | All,
    required: type[All] | All,
    user: Optional[User] = None,
    context: Optional[Base] = None,
    request: Optional[Request] = None,
) -> bool:
    """
    Check if a single granted permission covers the required permission.
    Supports class inheritance, composite groups, and context evaluation.
    """
    granted_cls = granted if isinstance(granted, type) else granted.__class__
    required_cls = required if isinstance(required, type) else required.__class__

    if issubclass(required_cls, granted_cls):
        if not _eval_context_check(granted, user=user, context=context, request=request):
            return False
        if not _eval_context_check(required, user=user, context=context, request=request):
            return False
        return True

    if hasattr(granted, "group") and isinstance(granted.group, (list, tuple, set)):
        return any(
            _check_single_permission(g, required, user=user, context=context, request=request)
            for g in granted.group
        )
    return False


def get_user_permissions(
    user: User, context: Optional[Base]
) -> list[type[All] | All]:
    """
    Get the list of granted permission classes or instances for a user in the given context.
    Context is required (e.g. model object or None).
    - Superadmin users receive root All (covers all permissions).
    - If user has get_permissions method, calls user.get_permissions(context).
    - If user has permissions attribute, resolve to permission classes or instances.
    - Regular authenticated users default to Read permission (covers List and View).
    """
    if getattr(user, "is_superadmin", False):
        return [All]

    if hasattr(user, "get_permissions") and callable(user.get_permissions):
        resolved: list[type[All] | All] = []
        user_perms = user.get_permissions(context)
        for p in user_perms:
            if isinstance(p, type) and issubclass(p, All):
                resolved.append(p)
            elif isinstance(p, All):
                resolved.append(p)
            elif isinstance(p, str) and p.lower() in _NAME_TO_PERMISSION:
                resolved.append(_NAME_TO_PERMISSION[p.lower()])
        return resolved

    if hasattr(user, "permissions") and user.permissions is not None:
        resolved = []
        for p in user.permissions:
            if isinstance(p, type) and issubclass(p, All):
                resolved.append(p)
            elif isinstance(p, All):
                resolved.append(p)
            elif isinstance(p, str) and p.lower() in _NAME_TO_PERMISSION:
                resolved.append(_NAME_TO_PERMISSION[p.lower()])
        return resolved

    return [Read]


def check_user_permission(
    user: Optional[User],
    perm: type[All] | str | All,
    request: Request | None = None,
    context: Optional[Base] = None,
) -> bool:
    """
    Evaluate if user has the requested permission using class inheritance and optional context.
    If the user has a granted permission class P_granted, and the requested
    permission is P_req, access is allowed if issubclass(P_req, P_granted) and any context
    checks pass.
    """
    # Allow passing context as 3rd positional argument if request is not a Request
    if request is not None and not isinstance(request, Request) and context is None:
        context = request
        request = None

    if user is None and request is not None:
        if hasattr(request, "state") and getattr(request.state, "user", None) is not None:
            user = request.state.user
        elif hasattr(request, "user") and getattr(request, "user", None) is not None:
            user = request.user

    if user is None:
        return False

    if context is None and request is not None and hasattr(request, "state"):
        context = getattr(request.state, "context", getattr(request.state, "model", None))

    if isinstance(perm, str):
        perm_cls = _NAME_TO_PERMISSION.get(perm.lower())
        if perm_cls is None:
            return False
    elif isinstance(perm, type) and issubclass(perm, All):
        perm_cls = perm
    elif isinstance(perm, All):
        perm_cls = perm
    else:
        return False

    if getattr(user, "is_superadmin", False):
        return True

    if hasattr(user, "has_permission") and callable(user.has_permission):
        try:
            sig = inspect.signature(user.has_permission)
            kwargs = {}
            if "context" in sig.parameters:
                kwargs["context"] = context
            if "request" in sig.parameters:
                kwargs["request"] = request
            if kwargs:
                return user.has_permission(perm_cls, **kwargs)
            if len(sig.parameters) >= 2:
                return user.has_permission(perm_cls, context)
            return user.has_permission(perm_cls)
        except Exception:
            pass

    try:
        granted_perms = get_user_permissions(user, context=context)
    except TypeError:
        granted_perms = get_user_permissions(user, context)
    for granted in granted_perms:
        if _check_single_permission(
            granted, perm_cls, user=user, context=context, request=request
        ):
            return True

    return False


async def has_permission(
    request: Request,
    perm: type[All] | str | All,
    context: Optional[Base] = None,
    user: Optional[User] = None,
    session: Optional[AsyncSession] = None,
) -> bool:
    """
    Check if the current request (or specified user) has the requested permission
    for the given context (model object).

    :param request: The incoming FastAPI/Starlette Request.
    :param perm: The permission class, string name, or permission instance to check.
    :param context: Optional context object (model instance) the permission applies to.
    :param user: Optional user object. If not specified, it is retrieved from the request.
    :param session: Optional AsyncSession for database lookup if user needs to be fetched.
    :return: True if permission is granted, False otherwise.
    """
    if not settings.enable_auth:
        return True

    # Handle backward compatibility if someone passes (request, perm, user, session) positionally
    if isinstance(user, SQLModelAsyncSession):
        session = user
        user = context
        context = None

    if context is None and hasattr(request, "state"):
        context = getattr(request.state, "context", getattr(request.state, "model", None))

    if user is None:
        if hasattr(request, "state") and getattr(request.state, "user", None) is not None:
            user = request.state.user
        elif hasattr(request, "user") and getattr(request, "user", None) is not None:
            user = request.user
        else:
            try:
                if session is not None:
                    user = await get_current_user(request, session)
                else:
                    async with SQLModelAsyncSession(get_engine()) as db_session:
                        user = await get_current_user(request, db_session)
                if hasattr(request, "state"):
                    request.state.user = user
            except Exception:
                return False

    if user is None:
        return False

    return check_user_permission(user, perm, request=request, context=context)


def require(
    perm: type[All] | str | All,
    context: Optional[Base] = None,
    context_getter: Optional[Callable] = None,
) -> params.Depends:
    """
    FastAPI dependency that enforces the given permission.
    Supports optional context or context_getter.
    Returns Depends(...) directly for clean syntax: dependencies=extra_deps + [require(Create)].
    """
    async def permission_checker(
        request: Request,
        session: AsyncSession,
    ):
        if not settings.enable_auth:
            return None

        ctx = context
        if ctx is None and context_getter is not None:
            if asyncio.iscoroutinefunction(context_getter):
                ctx = await context_getter(request, session)
            else:
                ctx = context_getter(request, session)
        if ctx is None and hasattr(request, "state"):
            ctx = getattr(request.state, "context", getattr(request.state, "model", None))

        allowed = await has_permission(
            request=request,
            perm=perm,
            context=ctx,
            session=session,
        )
        if not allowed:
            if isinstance(perm, str):
                perm_name = perm.lower()
            elif isinstance(perm, type) and issubclass(perm, All):
                perm_name = getattr(perm, "name", perm.__name__.lower())
            elif isinstance(perm, All):
                perm_name = getattr(perm, "name", perm.__class__.__name__.lower())
            else:
                perm_name = str(perm)
            raise HTTPException(
                status_code=403,
                detail=f"Permission denied for '{perm_name}'",
            )
        return getattr(request.state, "user", None)

    return Depends(permission_checker)

