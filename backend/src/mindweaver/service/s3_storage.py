from . import NamedBase, Base
from .base import ProjectScopedNamedBase, ProjectScopedService
from sqlalchemy import String
from sqlalchemy_utils import JSONType
from sqlmodel import Field, Relationship
from typing import Any, Literal, Union, Optional
from pydantic import BaseModel, HttpUrl, field_validator, ValidationError
from fastapi import HTTPException, Depends
from mindweaver.crypto import encrypt_password, decrypt_password, EncryptionError
import httpx
import boto3
from botocore.exceptions import ClientError, NoCredentialsError


# S3 Configuration schema
class S3Config(BaseModel):
    """Configuration schema for S3-based storage."""

    bucket: str
    region: str
    access_key: str
    secret_key: Optional[str] = None
    endpoint_url: Optional[str] = None  # For S3-compatible services

    @field_validator("bucket")
    @classmethod
    def validate_bucket(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Bucket name cannot be empty")
        # Basic bucket name validation (lowercase, no spaces, etc.)
        if not v.replace("-", "").replace(".", "").isalnum():
            raise ValueError(
                "Bucket name must contain only lowercase letters, numbers, hyphens, and dots"
            )
        return v.strip().lower()

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
    parameters: dict[str, Any] = Field(sa_type=JSONType())


class S3StorageService(ProjectScopedService[S3Storage]):

    @classmethod
    def model_class(cls) -> type[S3Storage]:
        return S3Storage

    def _validate_parameters(
        self,
        parameters: dict[str, Any],
        encrypt_passwords: bool = True,
    ) -> dict[str, Any]:
        """
        Validate S3 configuration parameters.

        Args:
            parameters: The parameters to validate
            encrypt_passwords: Whether to encrypt secret_key field (default: True)

        Returns:
            Validated parameters as a dictionary

        Raises:
            HTTPException: If validation fails
        """
        try:
            config = S3Config(**parameters)
            # Encrypt secret_key if present and encryption is enabled
            if encrypt_passwords and config.secret_key:
                try:
                    encrypted_secret = encrypt_password(config.secret_key)
                    # Return dict with encrypted secret
                    validated_dict = config.model_dump()
                    validated_dict["secret_key"] = encrypted_secret
                    return validated_dict
                except EncryptionError as e:
                    raise HTTPException(
                        status_code=500,
                        detail=f"Failed to encrypt secret key: {str(e)}",
                    )

            # Return validated parameters as dict
            return config.model_dump()

        except ValidationError as e:
            # Extract validation errors and format them nicely
            error_messages = []
            for error in e.errors():
                field = error["loc"][0] if error["loc"] else "unknown"
                message = error["msg"]
                error_messages.append(f"{field}: {message}")

            raise HTTPException(
                status_code=422,
                detail=f"Parameter validation failed: {'; '.join(error_messages)}",
            )

    async def create(self, data: NamedBase) -> S3Storage:
        """
        Create a new S3 storage with parameter validation.

        Args:
            data: NamedBase model containing name, title, and parameters

        Returns:
            Created S3Storage instance

        Raises:
            HTTPException: If validation fails
        """
        # Convert to dict to access fields
        data_dict = data.model_dump() if hasattr(data, "model_dump") else dict(data)

        # Extract and validate parameters
        parameters = data_dict.get("parameters", {})
        validated_parameters = self._validate_parameters(parameters)

        # Update the data object with validated parameters
        if hasattr(data, "parameters"):
            data.parameters = validated_parameters

        # Call parent create method
        return await super().create(data)

    async def update(self, model_id: int, data: NamedBase) -> S3Storage:
        """
        Update an existing S3 storage with parameter validation.

        Args:
            model_id: ID of the S3 storage to update
            data: NamedBase model containing fields to update

        Returns:
            Updated S3Storage instance

        Raises:
            HTTPException: If validation fails
        """
        # Convert to dict to access fields
        data_dict = (
            data.model_dump(exclude_unset=True)
            if hasattr(data, "model_dump")
            else dict(data)
        )

        # Fetch existing record to get current values
        existing = await self.get(model_id)
        if not existing:
            raise HTTPException(status_code=404, detail="S3 storage not found")

        # If parameters are being updated, validate them
        if "parameters" in data_dict:
            parameters = data_dict.get("parameters", {})

            # Special handling for secret_key to manage password retention
            secret_key = parameters.get("secret_key")
            retain_existing_secret = False

            # If secret_key is the special marker, clear it
            if secret_key == "__CLEAR_SECRET_KEY__":
                parameters["secret_key"] = ""
            # If secret_key is empty or not provided, retain existing secret_key
            elif not secret_key:
                # Get existing secret_key from stored parameters
                existing_secret = existing.parameters.get("secret_key", "")
                parameters["secret_key"] = existing_secret
                retain_existing_secret = True  # Don't re-encrypt
            # Otherwise, secret_key is being updated (will be encrypted in validation)

            # Validate parameters, but skip encryption if retaining existing secret
            validated_parameters = self._validate_parameters(
                parameters, encrypt_passwords=not retain_existing_secret
            )
            # Update the data object with validated parameters
            if hasattr(data, "parameters"):
                data.parameters = validated_parameters

        # Call parent update method
        return await super().update(model_id, data)


router = S3StorageService.router()


class TestConnectionRequest(BaseModel):
    parameters: dict[str, Any]
    storage_id: Optional[int] = None  # Optional ID to fetch stored secret


@router.post(
    f"{S3StorageService.service_path()}/test_connection",
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
    parameters = data.parameters.copy()  # Make a copy to avoid mutating original

    # If storage_id is provided, check for stored secret_key
    if data.storage_id:
        secret_key = parameters.get("secret_key")
        # If no secret_key provided, fetch from database
        if not secret_key:
            existing = await svc.get(data.storage_id)
            if existing and existing.parameters.get("secret_key"):
                # Use the stored encrypted secret
                stored_secret = existing.parameters.get("secret_key")
                # Decrypt it for testing
                try:
                    decrypted_secret = decrypt_password(stored_secret)
                    parameters["secret_key"] = decrypted_secret
                except EncryptionError:
                    # If decryption fails, continue without secret
                    pass

    try:
        # Validate S3 configuration
        bucket = parameters.get("bucket")
        region = parameters.get("region")
        access_key = parameters.get("access_key")
        secret_key = parameters.get("secret_key")
        endpoint_url = parameters.get("endpoint_url")

        if not bucket:
            raise ValueError("Bucket name is required")
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

            # Try to head the bucket to verify access
            s3_client.head_bucket(Bucket=bucket)

            return {
                "status": "success",
                "message": f"Successfully connected to S3 bucket '{bucket}' in region '{region}'",
            }

        except NoCredentialsError:
            raise ValueError("Invalid AWS credentials")
        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code", "Unknown")
            if error_code == "404":
                raise ValueError(f"Bucket '{bucket}' not found")
            elif error_code == "403":
                raise ValueError(f"Access denied to bucket '{bucket}'")
            else:
                raise ValueError(f"S3 connection failed: {str(e)}")

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
