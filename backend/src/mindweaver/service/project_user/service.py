# SPDX-FileCopyrightText: Copyright © 2026 Mohd Izhar Firdaus Bin Ismail
# SPDX-License-Identifier: AGPLv3+

import hashlib
import bcrypt
from typing import Any, Optional
from fastapi import Depends
from mindweaver.fw.service import Service, before_create, before_update
from mindweaver.fw.exc import FieldValidationError
from mindweaver.service.base import x_project_id
from .model import ProjectLocalUser, ProjectLocalUserSchema


def generate_hashes(password: str) -> dict[str, str]:
    """
    Generate bcrypt, md5, sha256, and sha512 hashes for a plaintext password.
    """
    password_bytes = password.encode("utf-8")
    salt = bcrypt.gensalt()
    bcrypt_hash = bcrypt.hashpw(password_bytes, salt).decode("utf-8")
    md5_hash = hashlib.md5(password_bytes).hexdigest()
    sha256_hash = hashlib.sha256(password_bytes).hexdigest()
    sha512_hash = hashlib.sha512(password_bytes).hexdigest()
    return {
        "password_hash_bcrypt": bcrypt_hash,
        "password_hash_md5": md5_hash,
        "password_hash_sha256": sha256_hash,
        "password_hash_sha512": sha512_hash,
    }


class ProjectLocalUserService(Service[ProjectLocalUser]):
    """
    Service class managing project-scoped local users.
    """

    @classmethod
    def model_class(cls) -> type[ProjectLocalUser]:
        """
        Return the SQLModel class for this service.
        """
        return ProjectLocalUser

    @classmethod
    def schema_class(cls) -> type[ProjectLocalUserSchema]:
        """
        Return the validation/form schema class for local users.
        """
        return ProjectLocalUserSchema

    async def validate_data(
        self, data: Any, mode: Optional[str] = None
    ) -> Any:
        """
        Validate password confirmation matches password.
        """
        data = await super().validate_data(data, mode)
        password = getattr(data, "password", None)
        password_confirm = getattr(data, "password_confirm", None)

        if password is not None and password != "__REDACTED__":
            if password != password_confirm:
                raise FieldValidationError(
                    field_location=["password_confirm"],
                    message="Passwords do not match"
                )
        return data

    @classmethod
    def service_path(cls) -> str:
        """
        Return the API base path for this service.
        """
        return "/project-local-users"

    @classmethod
    def extra_dependencies(cls):
        """
        Require X-Project-ID header for scoping actions.
        """
        return [Depends(x_project_id)]

    @classmethod
    def immutable_fields(cls) -> list[str]:
        """
        Define fields that cannot be modified after creation.
        """
        return super().immutable_fields() + ["project_id"]

    @classmethod
    def internal_fields(cls) -> list[str]:
        """
        Fields that are internal and not directly editable by the request schema.
        """
        return super().internal_fields() + [
            "password_hash_bcrypt",
            "password_hash_md5",
            "password_hash_sha256",
            "password_hash_sha512",
        ]

    @classmethod
    def widgets(cls) -> dict[str, Any]:
        """
        Define the form widgets for rendering.
        """
        return {
            "username": {"order": 1, "label": "Username", "type": "string"},
            "email": {"order": 2, "label": "Email", "type": "string"},
            "password": {"order": 3, "label": "Password", "type": "password"},
            "password_confirm": {"order": 4, "label": "Confirm Password", "type": "password"},
        }

    @before_create
    async def hash_password_create(self, model: ProjectLocalUser):
        """
        Hash password using multiple algorithms prior to saving to database.
        """
        if not model.password:
            raise ValueError("Password is required")

        hashes = generate_hashes(model.password)
        model.password_hash_bcrypt = hashes["password_hash_bcrypt"]
        model.password_hash_md5 = hashes["password_hash_md5"]
        model.password_hash_sha256 = hashes["password_hash_sha256"]
        model.password_hash_sha512 = hashes["password_hash_sha512"]
        model.password = None

    @before_update
    async def hash_password_update(self, model: ProjectLocalUser, data: Any):
        """
        Rehash password on update if a new password has been provided.
        """
        data_dict = data.model_dump(exclude_unset=True)
        if "password" in data_dict:
            val = data_dict["password"]
            if val == "__REDACTED__":
                # Preserve existing hashes
                pass
            elif not val or not val.strip():
                raise ValueError("Password cannot be empty")
            else:
                hashes = generate_hashes(val)
                model.password_hash_bcrypt = hashes["password_hash_bcrypt"]
                model.password_hash_md5 = hashes["password_hash_md5"]
                model.password_hash_sha256 = hashes["password_hash_sha256"]
                model.password_hash_sha512 = hashes["password_hash_sha512"]
            model.password = None

    async def post_process_model(self, model: ProjectLocalUser) -> ProjectLocalUser:
        """
        Redact password hash fields before returning data to the client.
        """
        model = await super().post_process_model(model)
        model_dict = model.model_dump()
        for field in [
            "password_hash_bcrypt",
            "password_hash_md5",
            "password_hash_sha256",
            "password_hash_sha512",
        ]:
            if field in model_dict:
                model_dict[field] = "__REDACTED__"
        return ProjectLocalUser.model_validate(model_dict)
