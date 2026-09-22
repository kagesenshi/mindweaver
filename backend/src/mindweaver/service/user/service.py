# SPDX-FileCopyrightText: Copyright © 2026 Mohd Izhar Firdaus Bin Ismail
# SPDX-License-Identifier: AGPLv3+

from typing import Any, Optional
from fastapi import Depends, HTTPException
from pydantic import BaseModel, Field as PydanticField
from mindweaver.fw.service import Service
from mindweaver.fw.auth import (
    User,
    get_current_user,
    get_superadmin,
    get_password_hash,
)
from mindweaver.fw.model import AsyncSession
from mindweaver.fw.util import redefine_model


class ChangePasswordRequest(BaseModel):
    """Payload schema for changing a user's password."""
    password: str = PydanticField(min_length=8)


class UserService(Service[User]):
    """
    Service managing application users.
    """

    @classmethod
    def model_class(cls) -> type[User]:
        """Return User SQLModel class."""
        return User

    @classmethod
    def hashed_fields(cls) -> list[str]:
        """Return fields that are hashed with password hasher."""
        return ["password"]

    @classmethod
    def immutable_fields(cls) -> list[str]:
        """Return fields that cannot be changed once created."""
        return ["name", "email"]

    @classmethod
    def updatemodel_class(cls):
        """Return dynamically generated update schema excluding password."""
        model_class = cls.model_class()
        schema_class = cls.schema_class()
        return redefine_model(
            f"Update {model_class.__name__}",
            schema_class,
            exclude=cls.internal_fields() + ["password"],
            optional=["__ALL__"],
        )

    @classmethod
    def widgets(cls) -> dict[str, Any]:
        """Return UI widgets configuration for user form."""
        return {
            "name": {"order": 1, "column_span": 1, "label": "Username"},
            "display_name": {"order": 2, "column_span": 1},
            "email": {"order": 3, "column_span": 1},
            "password": {"type": "password", "order": 4, "column_span": 1},
            "title": {"order": 5, "column_span": 1},
            "is_active": {"order": 6, "column_span": 1},
            "is_superadmin": {"order": 7, "column_span": 1},
        }

    @classmethod
    def extra_dependencies(cls):
        """Ensure only superadmins can access user management CRUD endpoints."""
        return [Depends(get_superadmin)]


@UserService.model_view("POST", "/_change_password", dependencies=[])
async def change_password(
    id: int,
    payload: ChangePasswordRequest,
    session: AsyncSession,
    current_user: User = Depends(get_current_user),
):
    """
    Change user password endpoint.
    Regular users can only change their own password; superadmins can change any user's password.
    """
    target_user = await session.get(User, id)
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found")

    if not current_user.is_superadmin and current_user.id != target_user.id:
        raise HTTPException(
            status_code=403,
            detail="Not authorized to change this user's password",
        )

    target_user.password = get_password_hash(payload.password)
    session.add(target_user)
    await session.commit()
    return {"status": "success", "message": "Password changed successfully"}
