# SPDX-FileCopyrightText: Copyright © 2026 Mohd Izhar Firdaus Bin Ismail
# SPDX-License-Identifier: AGPLv3+

from typing import Optional, Type
from fastapi import Depends, HTTPException, Request, params
from sqlmodel.ext.asyncio.session import AsyncSession as SQLModelAsyncSession
from mindweaver.config import settings
from mindweaver.fw.model import AsyncSession, get_engine
from mindweaver.fw.auth import User, get_current_user


class All:
    """Root permission class that all permissions inherit from."""
    name: str = "all"

    @classmethod
    def get_name(cls) -> str:
        """Return the lowercase name of the permission."""
        return getattr(cls, "name", cls.__name__.lower())


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


_NAME_TO_PERMISSION: dict[str, type[All]] = {
    "all": All,
    "admin": Admin,
    "permission": Permission,
    "read": Read,
    "list": List,
    "view": View,
    "write": Write,
    "create": Create,
    "update": Update,
    "delete": Delete,
    "execute": Execute,
}


def _check_single_permission(granted: type[All], required: type[All]) -> bool:
    """
    Check if a single granted permission class covers the required permission.
    Supports class inheritance (required is a subclass of granted) and composite groups.
    """
    if issubclass(required, granted):
        return True
    if hasattr(granted, "group") and isinstance(granted.group, (list, tuple, set)):
        return any(_check_single_permission(g, required) for g in granted.group)
    return False


def get_user_permissions(user: User) -> list[type[All]]:
    """
    Get the list of granted permission classes for a user.
    - Superadmin users receive root All (covers all permissions).
    - If user has permissions list or get_permissions method, resolve them to permission classes.
    - Regular authenticated users default to Read permission (covers List and View).
    """
    if getattr(user, "is_superadmin", False):
        return [All]

    if hasattr(user, "get_permissions") and callable(user.get_permissions):
        resolved = []
        for p in user.get_permissions():
            if isinstance(p, type) and issubclass(p, All):
                resolved.append(p)
            elif isinstance(p, str) and p.lower() in _NAME_TO_PERMISSION:
                resolved.append(_NAME_TO_PERMISSION[p.lower()])
        return resolved

    if hasattr(user, "permissions") and user.permissions is not None:
        resolved = []
        for p in user.permissions:
            if isinstance(p, type) and issubclass(p, All):
                resolved.append(p)
            elif isinstance(p, str) and p.lower() in _NAME_TO_PERMISSION:
                resolved.append(_NAME_TO_PERMISSION[p.lower()])
        return resolved

    return [Read]


def check_user_permission(
    user: Optional[User], perm: type[All] | str, request: Request | None = None
) -> bool:
    """
    Evaluate if user has the requested permission using class inheritance.
    If the user has a granted permission class P_granted, and the requested
    permission is P_req, access is allowed if issubclass(P_req, P_granted).
    """
    if user is None and request is not None:
        if hasattr(request, "state") and getattr(request.state, "user", None) is not None:
            user = request.state.user
        elif hasattr(request, "user") and getattr(request, "user", None) is not None:
            user = request.user

    if user is None:
        return False

    if isinstance(perm, str):
        perm_cls = _NAME_TO_PERMISSION.get(perm.lower())
        if perm_cls is None:
            return False
    elif isinstance(perm, type) and issubclass(perm, All):
        perm_cls = perm
    else:
        return False

    granted_perms = get_user_permissions(user)
    for granted in granted_perms:
        if _check_single_permission(granted, perm_cls):
            return True

    return False


async def has_permission(
    request: Request,
    perm: type[All] | str,
    user: Optional[User] = None,
    session: Optional[AsyncSession] = None,
) -> bool:
    """
    Check if the current request (or specified user) has the requested permission.

    :param request: The incoming FastAPI/Starlette Request.
    :param perm: The permission class or string name to check.
    :param user: Optional user object. If not specified, it is retrieved from the request.
    :param session: Optional AsyncSession for database lookup if user needs to be fetched.
    :return: True if permission is granted, False otherwise.
    """
    if not settings.enable_auth:
        return True

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

    return check_user_permission(user, perm, request)


def require(perm: type[All] | str) -> params.Depends:
    """
    FastAPI dependency that enforces the given permission.
    Returns Depends(...) directly for clean syntax: dependencies=extra_deps + [require(Create)].
    """
    async def permission_checker(
        request: Request,
        session: AsyncSession,
    ):
        if not settings.enable_auth:
            return None

        user = await get_current_user(request, session)
        if hasattr(request, "state"):
            request.state.user = user

        if not check_user_permission(user, perm, request):
            if isinstance(perm, str):
                perm_name = perm.lower()
            elif isinstance(perm, type) and issubclass(perm, All):
                perm_name = getattr(perm, "name", perm.__name__.lower())
            else:
                perm_name = str(perm)
            raise HTTPException(
                status_code=403,
                detail=f"Permission denied for '{perm_name}'",
            )
        return user

    return Depends(permission_checker)
