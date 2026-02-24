# SPDX-FileCopyrightText: Copyright © 2026 Mohd Izhar Firdaus Bin Ismail
# SPDX-License-Identifier: AGPLv3+

from mindweaver.service import NamedBase, Base
from mindweaver.service.base import ProjectScopedNamedBase, ProjectScopedService
from mindweaver.fw.service import SecretHandlerMixin
from mindweaver.config import settings
from sqlmodel import Field
from typing import Any, Optional
from pydantic import BaseModel, field_validator, ValidationError
from fastapi import HTTPException
from mindweaver.crypto import encrypt_password, decrypt_password, EncryptionError
from mindweaver.fw.exc import FieldValidationError


# S3 Configuration schema
class S3Config(BaseModel):
    """Configuration schema for S3-based storage."""

    region: str
    access_key: str
    secret_key: Optional[str] = None
    endpoint_url: Optional[str] = None  # For S3-compatible services
    verify_ssl: bool = True

    @field_validator("region")
    @classmethod
    def validate_region(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Region cannot be empty")
        return v.strip()

    @field_validator("access_key")
    @classmethod
    def validate_access_key(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Access key cannot be empty")
        return v.strip()

    @field_validator("endpoint_url")
    @classmethod
    def validate_endpoint_url(cls, v: Optional[str]) -> Optional[str]:
        if v and v.strip():
            # Basic URL validation
            if not (v.startswith("http://") or v.startswith("https://")):
                raise ValueError("Endpoint URL must start with http:// or https://")
            return v.strip()
        return v


# Database model
class S3Storage(ProjectScopedNamedBase, table=True):
    __tablename__ = "mw_s3_storage"
    region: str
    access_key: str
    secret_key: Optional[str] = Field(default=None)
    endpoint_url: Optional[str] = Field(default=None)
    verify_ssl: bool = Field(default=True)


class S3StorageService(SecretHandlerMixin, ProjectScopedService[S3Storage]):

    @classmethod
    def model_class(cls) -> type[S3Storage]:
        return S3Storage

    @classmethod
    def redacted_fields(cls) -> list[str]:
        return ["secret_key"]

    async def create(self, data: S3Storage) -> S3Storage:
        """
        Create a new S3 storage with validation.
        """
        # Validate core fields using S3Config
        try:
            # We dump the data to dict and validate with S3Config
            # Note: secret_key is not yet encrypted here
            S3Config(**data.model_dump())
        except ValidationError as e:
            error = e.errors()[0]
            field = error["loc"][0] if error["loc"] else "unknown"
            message = error["msg"]
            raise FieldValidationError(
                field_location=[field],
                message=message,
            )

        # Call parent create method which will handle encryption via RedactedServiceMixin
        return await super().create(data)

    async def update(self, model_id: int, data: S3Storage) -> S3Storage:
        """
        Update an existing S3 storage with validation.
        """
        # Fetch existing record
        existing = await self.get(model_id)
        if not existing:
            raise HTTPException(status_code=404, detail="S3 storage not found")

        # Convert to dict to check fields
        data_dict = (
            data.model_dump(exclude_unset=True)
            if hasattr(data, "model_dump")
            else dict(data)
        )

        # Merge with existing for validation
        merged_data = existing.model_dump()
        merged_data.update(data_dict)

        secret_is_encrypted = True
        secret_key = data_dict.get("secret_key")
        if secret_key:
            if secret_key == "__CLEAR__":
                merged_data["secret_key"] = ""
            elif secret_key == "__REDACTED__":
                merged_data["secret_key"] = existing.secret_key
            else:
                # New secret key provided
                merged_data["secret_key"] = secret_key
                secret_is_encrypted = False

        # Validate core fields
        try:
            v_data = merged_data.copy()
            if secret_is_encrypted and v_data.get("secret_key"):
                # Use a dummy secret for validation if it's already encrypted
                v_data["secret_key"] = "dummy"

            S3Config(**v_data)
        except ValidationError as e:
            error = e.errors()[0]
            field = error["loc"][0] if error["loc"] else "unknown"
            message = error["msg"]
            raise FieldValidationError(
                field_location=[field],
                message=message,
            )

        # Call parent update method which will handle encryption via RedactedServiceMixin
        return await super().update(model_id, data)

    def verify_secret_key(self, model: S3Storage, secret_key: str) -> bool:
        """
        Verify if the provided secret key matches the encrypted one in the model.
        """
        if not model.secret_key:
            return False
        try:
            return decrypt_password(model.secret_key) == secret_key
        except EncryptionError:
            return False

    @classmethod
    def widgets(cls) -> dict[str, Any]:
        return {
            "endpoint_url": {"order": 3},
            "verify_ssl": {"order": 4, "type": "boolean"},
            "region": {"order": 5},
            "access_key": {"order": 6},
            "secret_key": {"order": 7, "type": "password"},
        }
