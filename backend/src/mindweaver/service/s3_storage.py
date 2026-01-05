from . import NamedBase, Base
from .base import ProjectScopedNamedBase, ProjectScopedService
from mindweaver.config import settings
from sqlalchemy import String
from sqlalchemy_utils import JSONType
from sqlmodel import Field, Relationship
from typing import Any, Literal, Union, Optional, Annotated
from pydantic import BaseModel, HttpUrl, field_validator, ValidationError
import fastapi
from fastapi import HTTPException, Depends
from mindweaver.crypto import encrypt_password, decrypt_password, EncryptionError
import httpx
import boto3
from botocore.exceptions import ClientError, NoCredentialsError


# S3 Configuration schema
class S3Config(BaseModel):
    """Configuration schema for S3-based storage."""

    region: str
    access_key: str
    secret_key: Optional[str] = None
    endpoint_url: Optional[str] = None  # For S3-compatible services

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
    parameters: dict[str, Any] = Field(sa_type=JSONType(), default_factory=dict)


class VerifyEncryptedRequest(BaseModel):
    secret_key: str


class TestConnectionRequest(BaseModel):
    region: Optional[str] = None
    access_key: Optional[str] = None
    secret_key: Optional[str] = None
    endpoint_url: Optional[str] = None
    parameters: dict[str, Any] = Field(default_factory=dict)
    storage_id: Optional[int] = None


class S3StorageService(ProjectScopedService[S3Storage]):

    @classmethod
    def model_class(cls) -> type[S3Storage]:
        return S3Storage

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
            error_messages = []
            for error in e.errors():
                field = error["loc"][0] if error["loc"] else "unknown"
                message = error["msg"]
                error_messages.append(f"{field}: {message}")

            raise HTTPException(
                status_code=422,
                detail=f"Parameter validation failed: {'; '.join(error_messages)}",
            )

        # Encrypt secret_key if present
        if data.secret_key:
            try:
                data.secret_key = encrypt_password(data.secret_key)
            except EncryptionError as e:
                raise HTTPException(
                    status_code=500,
                    detail=f"Failed to encrypt secret key: {str(e)}",
                )

        # Call parent create method
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

        # Handle secret_key logic
        secret_is_encrypted = True
        if "secret_key" in data_dict:
            secret_key = data_dict["secret_key"]
            if secret_key == "__CLEAR_SECRET_KEY__":
                data.secret_key = ""
                merged_data["secret_key"] = ""
            elif not secret_key or secret_key == "__REDACTED__":
                # Retain existing secret_key
                data.secret_key = existing.secret_key
                merged_data["secret_key"] = existing.secret_key
            else:
                # New secret key provided (not yet encrypted in merged_data)
                merged_data["secret_key"] = secret_key
                secret_is_encrypted = False

        # Validate core fields
        try:
            # If secret is already encrypted, we might want to skip validating its format
            # but decrypting it for validation might be overkill if it was already valid.
            v_data = merged_data.copy()
            if secret_is_encrypted and v_data.get("secret_key"):
                # Use a dummy secret for validation if it's already encrypted
                v_data["secret_key"] = "dummy"

            S3Config(**v_data)
        except ValidationError as e:
            error_messages = []
            for error in e.errors():
                field = error["loc"][0] if error["loc"] else "unknown"
                message = error["msg"]
                error_messages.append(f"{field}: {message}")

            raise HTTPException(
                status_code=422,
                detail=f"Parameter validation failed: {'; '.join(error_messages)}",
            )

        # Now encrypt the secret_key if it's a new one
        if "secret_key" in data_dict and data.secret_key and not secret_is_encrypted:
            try:
                data.secret_key = encrypt_password(data.secret_key)
            except EncryptionError as e:
                raise HTTPException(
                    status_code=500,
                    detail=f"Failed to encrypt secret key: {str(e)}",
                )

        # Call parent update method
        return await super().update(model_id, data)

    def post_process_model(self, model: S3Storage) -> S3Storage:
        """
        Redact the secret key before returning to the client.
        """
        if model.secret_key:
            # Create a detached copy to avoid affecting the session
            model_dict = model.model_dump()
            if model_dict.get("secret_key"):
                model_dict["secret_key"] = "__REDACTED__"
            return S3Storage.model_validate(model_dict)
        return model

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
    def register_views(
        cls, router: fastapi.APIRouter, service_path: str, model_path: str
    ):
        super().register_views(router, service_path, model_path)

        path_tags = cls.path_tags()

        if settings.enable_test_views:

            @router.post(
                f"{model_path}/+verify-encrypted",
                operation_id=f"mw-verify-encrypted-{cls.entity_type()}",
                tags=path_tags,
            )
            async def verify_encrypted(
                svc: Annotated[cls, Depends(cls.get_service)],
                model: Annotated[S3Storage, Depends(cls.get_model)],
                data: VerifyEncryptedRequest,
            ) -> bool:
                return svc.verify_secret_key(model, data.secret_key)


router = S3StorageService.router()


@router.post(
    f"{S3StorageService.service_path()}/+test-connection",
    tags=S3StorageService.path_tags(),
)
async def test_connection(
    data: TestConnectionRequest,
    svc: S3StorageService = Depends(S3StorageService.get_service),
):
    """
    Test connection to S3 storage.
    If storage_id is provided and secret_key is missing, use stored secret.
    """
    # Initialize variables from request
    region = data.region or data.parameters.get("region")
    access_key = data.access_key or data.parameters.get("access_key")
    secret_key = data.secret_key or data.parameters.get("secret_key")
    endpoint_url = data.endpoint_url or data.parameters.get("endpoint_url")

    # If storage_id is provided, check for stored secret_key if missing in request
    if data.storage_id:
        existing = await svc.get(data.storage_id)
        if existing and existing.secret_key and not secret_key:
            try:
                # Note: svc.get now returns redacted secret_key, but we need the raw one.
                # However, svc.get calls super().get() which returns the raw one from the session.
                # Wait, svc.get is now NOT redacted anymore because I removed the override.
                secret_key = decrypt_password(existing.secret_key)
            except EncryptionError:
                pass

    try:
        if not region:
            raise ValueError("Region is required")
        if not access_key:
            raise ValueError("Access key is required")

        # Try to connect to S3 using boto3
        try:
            # Create S3 client
            s3_config = {
                "aws_access_key_id": access_key,
                "region_name": region,
            }

            if secret_key:
                s3_config["aws_secret_access_key"] = secret_key

            if endpoint_url:
                s3_config["endpoint_url"] = endpoint_url

            s3_client = boto3.client("s3", **s3_config)

            # Try to list buckets to verify access
            s3_client.list_buckets()

            return {
                "status": "success",
                "message": f"Successfully connected to S3 in region '{region}'",
            }

        except NoCredentialsError:
            raise ValueError("Invalid AWS credentials")
        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code", "Unknown")
            if error_code == "403":
                raise ValueError(f"Access denied: {str(e)}")
            else:
                raise ValueError(f"S3 connection failed: {str(e)}")

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
