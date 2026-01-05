from . import NamedBase, Base
from .base import ProjectScopedNamedBase, ProjectScopedService
from mindweaver.fw.service import Service
from sqlalchemy import String, Integer, DateTime, Enum as SQLEnum, ForeignKey
from sqlalchemy_utils import JSONType
from sqlmodel import Field, Relationship
from typing import Any, Literal, Optional
from pydantic import BaseModel, field_validator, ValidationError
from fastapi import HTTPException, Depends
from mindweaver.fw.exc import FieldValidationError, NotFoundError
from datetime import datetime, timezone
import enum
from croniter import croniter


# Enums for ingestion types and statuses
class IngestionType(str, enum.Enum):
    FULL_REFRESH = "full_refresh"
    INCREMENTAL = "incremental"


class IngestionRunStatus(str, enum.Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


# Configuration schemas
class DatabaseIngestionConfig(BaseModel):
    """Configuration for database ingestion."""

    table_name: str
    ingestion_type: IngestionType = IngestionType.FULL_REFRESH
    primary_keys: Optional[list[str]] = None
    last_modified_column: Optional[str] = None
    created_column: Optional[str] = None
    source_timezone: str = "UTC"

    @field_validator("table_name")
    @classmethod
    def validate_table_name(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Table name cannot be empty")
        return v.strip()

    def model_post_init(self, __context) -> None:
        """Validate incremental-specific fields after model initialization."""
        if self.ingestion_type == IngestionType.INCREMENTAL:
            if not self.primary_keys or len(self.primary_keys) == 0:
                raise ValueError("Primary keys are required for incremental ingestion")
            if not self.last_modified_column or not self.last_modified_column.strip():
                raise ValueError(
                    "Last modified column is required for incremental ingestion"
                )
            if not self.created_column or not self.created_column.strip():
                raise ValueError("Created column is required for incremental ingestion")


# Database models
class Ingestion(ProjectScopedNamedBase, table=True):
    """Ingestion configuration model."""

    __tablename__ = "mw_ingestion"

    data_source_id: int = Field(foreign_key="mw_datasource.id", index=True)
    s3_storage_id: int = Field(foreign_key="mw_s3_storage.id", index=True)
    storage_path: str = Field(max_length=500)
    cron_schedule: str = Field(max_length=100)
    start_date: Optional[datetime] = Field(default=None)
    end_date: Optional[datetime] = Field(default=None)
    timezone: str = Field(default="UTC", max_length=50)
    ingestion_type: str = Field(max_length=50)  # "full_refresh" or "incremental"
    config: dict[str, Any] = Field(sa_type=JSONType())


class IngestionRun(Base, table=True):
    """Ingestion run execution history and metadata."""

    __tablename__ = "mw_ingestion_run"

    ingestion_id: int = Field(foreign_key="mw_ingestion.id", index=True)
    status: str = Field(
        max_length=50, index=True
    )  # pending, running, completed, failed
    started_at: Optional[datetime] = Field(default=None)
    completed_at: Optional[datetime] = Field(default=None)
    records_processed: int = Field(default=0)
    error_message: Optional[str] = Field(default=None, max_length=1000)
    watermark_metadata: dict[str, Any] = Field(sa_type=JSONType(), default={})


class IngestionService(ProjectScopedService[Ingestion]):

    @classmethod
    def model_class(cls) -> type[Ingestion]:
        return Ingestion

    def _validate_cron_schedule(self, cron_schedule: str) -> None:
        """
        Validate that the cron schedule is valid.

        Args:
            cron_schedule: The cron schedule string to validate

        Raises:
            HTTPException: If the cron schedule is invalid
        """
        if not cron_schedule or not cron_schedule.strip():
            raise FieldValidationError(
                field_location=["cron_schedule"],
                message="Cron schedule cannot be empty",
            )

        try:
            # croniter will raise ValueError if the cron expression is invalid
            croniter(cron_schedule)
        except (ValueError, KeyError) as e:
            raise FieldValidationError(
                field_location=["cron_schedule"],
                message=f"Invalid cron schedule '{cron_schedule}': {str(e)}",
            )

    def _validate_config(
        self,
        data_source_type: str,
        config: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Validate ingestion configuration based on data source type.

        Args:
            data_source_type: The type of data source (API, Database, etc.)
            config: The configuration to validate

        Returns:
            Validated configuration as a dictionary

        Raises:
            HTTPException: If validation fails
        """
        try:
            # Only Database sources support ingestion configuration
            if data_source_type == "Database":
                validated_config = DatabaseIngestionConfig(**config)
                return validated_config.model_dump()
            else:
                # For non-database sources, config can be empty or minimal
                return config

        except ValidationError as e:
            error = e.errors()[0]
            field = error["loc"][0] if error["loc"] else "unknown"
            message = error["msg"]
            raise FieldValidationError(
                field_location=[field],
                message=message,
            )

    async def create(self, data: NamedBase) -> Ingestion:
        """
        Create a new ingestion with configuration validation.

        Args:
            data: NamedBase model containing ingestion configuration

        Returns:
            Created Ingestion instance

        Raises:
            HTTPException: If validation fails
        """
        # Convert to dict to access fields
        data_dict = data.model_dump() if hasattr(data, "model_dump") else dict(data)

        # Validate required fields
        if not data_dict.get("data_source_id"):
            raise FieldValidationError(
                field_location=["data_source_id"], message="Data source ID is required"
            )
        if not data_dict.get("s3_storage_id"):
            raise FieldValidationError(
                field_location=["s3_storage_id"], message="S3 storage ID is required"
            )
        if not data_dict.get("storage_path"):
            raise FieldValidationError(
                field_location=["storage_path"], message="Storage path is required"
            )
        if not data_dict.get("cron_schedule"):
            raise FieldValidationError(
                field_location=["cron_schedule"], message="Cron schedule is required"
            )

        # Validate cron schedule format
        self._validate_cron_schedule(data_dict["cron_schedule"])

        # Fetch the data source to get its type
        from .data_source import DataSourceService

        ds_service = DataSourceService(self.request, self.session)
        data_source = await ds_service.get(data_dict["data_source_id"])
        if not data_source:
            raise NotFoundError(message="Data source not found")

        # Validate configuration based on data source type
        config = data_dict.get("config", {})
        validated_config = self._validate_config(data_source.type, config)

        # Update the data object with validated config
        if hasattr(data, "config"):
            data.config = validated_config

        # Call parent create method
        return await super().create(data)

    async def update(self, model_id: int, data: NamedBase) -> Ingestion:
        """
        Update an existing ingestion with configuration validation.

        Args:
            model_id: ID of the ingestion to update
            data: NamedBase model containing fields to update

        Returns:
            Updated Ingestion instance

        Raises:
            HTTPException: If validation fails
        """
        # Convert to dict to access fields
        data_dict = (
            data.model_dump(exclude_unset=True)
            if hasattr(data, "model_dump")
            else dict(data)
        )

        # Fetch existing record
        existing = await self.get(model_id)
        if not existing:
            raise NotFoundError(message="Ingestion not found")

        # Validate cron schedule if it's being updated
        if "cron_schedule" in data_dict:
            self._validate_cron_schedule(data_dict["cron_schedule"])

        # If config is being updated, validate it
        if "config" in data_dict:
            # Get data source type (either from update or existing)
            data_source_id = data_dict.get("data_source_id", existing.data_source_id)

            from .data_source import DataSourceService

            ds_service = DataSourceService(self.request, self.session)
            data_source = await ds_service.get(data_source_id)
            if not data_source:
                raise NotFoundError(message="Data source not found")

            config = data_dict.get("config", {})
            validated_config = self._validate_config(data_source.type, config)

            # Update the data object with validated config
            if hasattr(data, "config"):
                data.config = validated_config

        # Call parent update method
        return await super().update(model_id, data)


class IngestionRunService(Service[IngestionRun]):

    @classmethod
    def model_class(cls) -> type[IngestionRun]:
        return IngestionRun


# Create routers
router = IngestionService.router()
run_router = IngestionRunService.router()


# Custom endpoints
@router.post(
    f"{IngestionService.service_path()}/{{ingestion_id}}/execute",
    tags=IngestionService.path_tags(),
)
async def execute_ingestion(
    ingestion_id: int,
    svc: IngestionService = Depends(IngestionService.get_service),
):
    """
    Trigger manual execution of an ingestion.

    This endpoint creates a new IngestionRun record and would trigger
    the actual ingestion process (to be implemented with a task queue).
    """
    # Verify ingestion exists
    ingestion = await svc.get(ingestion_id)
    if not ingestion:
        raise NotFoundError(message="Ingestion not found")

    # Create a new run record
    run_service = IngestionRunService(svc.request, svc.session)
    new_run = await run_service.create(
        IngestionRun(
            ingestion_id=ingestion_id,
            status=IngestionRunStatus.PENDING.value,
            started_at=datetime.now(timezone.utc).replace(tzinfo=None),
            records_processed=0,
            watermark_metadata={},
        )
    )

    # TODO: Trigger actual ingestion execution via task queue
    # For now, just return the created run

    return {
        "status": "success",
        "message": "Ingestion execution triggered",
        "record": new_run,
    }


@router.get(
    f"{IngestionService.service_path()}/{{ingestion_id}}/runs",
    tags=IngestionService.path_tags(),
)
async def list_ingestion_runs(
    ingestion_id: int,
    svc: IngestionService = Depends(IngestionService.get_service),
):
    """
    List all execution runs for a specific ingestion.
    """
    # Verify ingestion exists
    ingestion = await svc.get(ingestion_id)
    if not ingestion:
        raise NotFoundError(message="Ingestion not found")

    # Query runs for this ingestion
    from sqlmodel import select

    run_service = IngestionRunService(svc.request, svc.session)

    statement = (
        select(IngestionRun)
        .where(IngestionRun.ingestion_id == ingestion_id)
        .order_by(IngestionRun.created.desc())
    )
    results = await svc.session.execute(statement)
    runs = results.scalars().all()

    return {
        "status": "success",
        "records": runs,
    }
