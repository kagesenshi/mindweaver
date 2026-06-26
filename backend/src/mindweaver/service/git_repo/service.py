# SPDX-FileCopyrightText: Copyright © 2026 Mohd Izhar Firdaus Bin Ismail
# SPDX-License-Identifier: AGPLv3+

from mindweaver.service.base import ProjectScopedService
from mindweaver.fw.exc import FieldValidationError
from pydantic import ValidationError
from typing import Any
from fastapi import HTTPException

from .model import GitRepo, GitRepoConfig


class GitRepoService(ProjectScopedService[GitRepo]):
    """Service for managing external Git repository connections."""

    @classmethod
    def model_class(cls) -> type[GitRepo]:
        return GitRepo

    @classmethod
    def redacted_fields(cls) -> list[str]:
        return ["password"]

    async def create(self, data: GitRepo) -> GitRepo:
        """
        Create a new Git connection with validation.
        """
        try:
            GitRepoConfig(**data.model_dump())
        except ValidationError as e:
            error = e.errors()[0]
            field = error["loc"][0] if error["loc"] else "unknown"
            message = error["msg"]
            raise FieldValidationError(
                field_location=[field],
                message=message,
            )
        return await super().create(data)

    async def update(self, model_id: int, data: GitRepo) -> GitRepo:
        """
        Update an existing Git connection with validation.
        """
        existing = await self.get(model_id)
        if not existing:
            raise HTTPException(status_code=404, detail="Git repository connection not found")

        data_dict = (
            data.model_dump(exclude_unset=True)
            if hasattr(data, "model_dump")
            else dict(data)
        )

        merged_data = existing.model_dump()
        merged_data.update(data_dict)

        secret_is_encrypted = True
        password = data_dict.get("password")
        if password:
            if password == "__CLEAR__":
                merged_data["password"] = ""
            elif password == "__REDACTED__":
                merged_data["password"] = existing.password
            else:
                merged_data["password"] = password
                secret_is_encrypted = False

        try:
            v_data = merged_data.copy()
            if secret_is_encrypted and v_data.get("password"):
                v_data["password"] = "dummy"

            GitRepoConfig(**v_data)
        except ValidationError as e:
            error = e.errors()[0]
            field = error["loc"][0] if error["loc"] else "unknown"
            message = error["msg"]
            raise FieldValidationError(
                field_location=[field],
                message=message,
            )

        return await super().update(model_id, data)

    @classmethod
    def widgets(cls) -> dict[str, Any]:
        return {
            "url": {
                "order": 3,
                "label": "Repository URL",
                "placeholder": "https://github.com/org/repo.git or git@github.com:org/repo.git",
            },
            "username": {
                "order": 4,
                "label": "Username",
                "placeholder": "Omit for token-only auth",
            },
            "password": {
                "order": 5,
                "type": "password",
                "label": "Password / Personal Access Token",
            },
            "ssh_key_id": {
                "order": 6,
                "type": "relationship",
                "endpoint": "/api/v1/ssh_keys",
                "label": "SSH Key",
                "field": "id",
            },
        }
