from . import NamedBase, Base
from . import Service
from sqlalchemy import String
from sqlalchemy_utils import JSONType
from sqlmodel import Field, Relationship
from typing import Any, Literal, Union
from pydantic import BaseModel, HttpUrl, field_validator, ValidationError
from fastapi import HTTPException

# Source type literal
SourceType = Literal["API", "Database", "File Upload", "Web Scraper"]


# Parameter schemas for different source types
class APIConfig(BaseModel):
    """Configuration schema for API data sources."""

    base_url: str
    api_key: str

    @field_validator("base_url")
    @classmethod
    def validate_base_url(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Base URL cannot be empty")
        # Basic URL validation
        if not (v.startswith("http://") or v.startswith("https://")):
            raise ValueError("Base URL must start with http:// or https://")
        return v.strip()

    @field_validator("api_key")
    @classmethod
    def validate_api_key(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("API key cannot be empty")
        return v.strip()


class DBConfig(BaseModel):
    """Configuration schema for Database data sources."""

    host: str
    port: int
    username: str

    @field_validator("host")
    @classmethod
    def validate_host(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Host cannot be empty")
        return v.strip()

    @field_validator("port")
    @classmethod
    def validate_port(cls, v: int) -> int:
        if v <= 0 or v > 65535:
            raise ValueError("Port must be between 1 and 65535")
        return v

    @field_validator("username")
    @classmethod
    def validate_username(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Username cannot be empty")
        return v.strip()


class WebScraperConfig(BaseModel):
    """Configuration schema for Web Scraper data sources."""

    start_url: str

    @field_validator("start_url")
    @classmethod
    def validate_start_url(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Start URL cannot be empty")
        # Basic URL validation
        if not (v.startswith("http://") or v.startswith("https://")):
            raise ValueError("Start URL must start with http:// or https://")
        return v.strip()


class FileUploadConfig(BaseModel):
    """Configuration schema for File Upload data sources."""

    # File upload doesn't require specific configuration parameters
    pass


# Database model
class DataSource(NamedBase, table=True):
    __tablename__ = "mw_datasource"
    type: str = Field(index=True)
    parameters: dict[str, Any] = Field(sa_type=JSONType())


class DataSourceService(Service[DataSource]):

    @classmethod
    def model_class(cls) -> type[DataSource]:
        return DataSource

    def _validate_parameters(
        self, source_type: str, parameters: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Validate parameters based on source type.

        Args:
            source_type: The type of data source
            parameters: The parameters to validate

        Returns:
            Validated parameters as a dictionary

        Raises:
            HTTPException: If validation fails
        """
        try:
            if source_type == "API":
                config = APIConfig(**parameters)
            elif source_type == "Database":
                config = DBConfig(**parameters)
            elif source_type == "Web Scraper":
                config = WebScraperConfig(**parameters)
            elif source_type == "File Upload":
                config = FileUploadConfig(**parameters)
            else:
                raise HTTPException(
                    status_code=422,
                    detail=f"Invalid source type: {source_type}. Must be one of: API, Database, File Upload, Web Scraper",
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

    async def create(self, data: NamedBase) -> DataSource:
        """
        Create a new data source with parameter validation.

        Args:
            data: NamedBase model containing name, title, type, and parameters

        Returns:
            Created DataSource instance

        Raises:
            HTTPException: If validation fails
        """
        # Convert to dict to access fields
        data_dict = data.model_dump() if hasattr(data, "model_dump") else dict(data)

        # Extract and validate source type
        source_type = data_dict.get("type")
        if not source_type:
            raise HTTPException(status_code=422, detail="Source type is required")

        # Extract and validate parameters
        parameters = data_dict.get("parameters", {})
        validated_parameters = self._validate_parameters(source_type, parameters)

        # Update the data object with validated parameters
        if hasattr(data, "parameters"):
            data.parameters = validated_parameters

        # Call parent create method
        return await super().create(data)

    async def update(self, model_id: int, data: NamedBase) -> DataSource:
        """
        Update an existing data source with parameter validation.

        Args:
            model_id: ID of the data source to update
            data: NamedBase model containing fields to update

        Returns:
            Updated DataSource instance

        Raises:
            HTTPException: If validation fails
        """
        # Convert to dict to access fields
        data_dict = (
            data.model_dump(exclude_unset=True)
            if hasattr(data, "model_dump")
            else dict(data)
        )

        # If type is being updated, validate it
        source_type = data_dict.get("type")

        # If type is not in the update data, fetch the existing record to get the type
        if not source_type:
            existing = await self.get(model_id)
            if existing:
                source_type = existing.type

        # If parameters are being updated, validate them
        if "parameters" in data_dict and source_type:
            parameters = data_dict.get("parameters", {})
            validated_parameters = self._validate_parameters(source_type, parameters)
            # Update the data object with validated parameters
            if hasattr(data, "parameters"):
                data.parameters = validated_parameters

        # Call parent update method
        return await super().update(model_id, data)


router = DataSourceService.router()
