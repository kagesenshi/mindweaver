from . import NamedBase
from .base import ProjectScopedNamedBase, ProjectScopedService
from mindweaver.fw.service import SecretHandlerMixin
from sqlalchemy import String, Text, Boolean
from sqlalchemy_utils import JSONType
from sqlmodel import Field
from typing import Any, Literal, Optional
from pydantic import BaseModel
from fastapi import HTTPException, Depends
from mindweaver.fw.exc import MindWeaverError
from mindweaver.crypto import encrypt_password, decrypt_password, EncryptionError
import httpx
import asyncio
from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL
from mindweaver.ext.data_source import get_driver_options, get_driver


class DataSource(ProjectScopedNamedBase, table=True):
    __tablename__ = "mw_datasource"

    description: Optional[str] = Field(
        default=None, sa_type=Text, sa_column_kwargs={"info": {"column_span": 2}}
    )
    driver: str = Field(
        sa_type=String(length=50),
        description="Source type / driver (e.g. web, postgresql, trino)",
        sa_column_kwargs={
            "info": {
                "widget": "select",
                "label": "Driver",
            }
        },
    )
    host: Optional[str] = Field(default=None, sa_type=String(length=255))
    port: Optional[int] = Field(default=None)
    resource: Optional[str] = Field(
        default=None,
        sa_type=String(length=500),
        description="Path, database name, schema, etc.",
    )
    login: Optional[str] = Field(default=None, sa_type=String(length=255))
    password: Optional[str] = Field(
        default=None,
        sa_type=String(length=500),
        sa_column_kwargs={"info": {"widget": "password"}},
    )
    enable_ssl: bool = Field(default=False, sa_type=Boolean)
    verify_ssl: bool = Field(default=False, sa_type=Boolean)
    parameters: dict[str, Any] = Field(
        default={},
        sa_type=JSONType(),
        description="Extra driver parameters (querystring format)",
    )


class DataSourceService(SecretHandlerMixin, ProjectScopedService[DataSource]):
    @classmethod
    def model_class(cls) -> type[DataSource]:
        return DataSource

    @classmethod
    def widgets(cls) -> dict[str, Any]:
        return {
            "driver": {"type": "select", "options": get_driver_options()},
            "password": {"type": "password"},
            "parameters": {"type": "key-value"},
        }

    @classmethod
    def redacted_fields(cls) -> list[str]:
        return ["password"]

    async def update(self, model_id: int, data: NamedBase) -> DataSource:
        return await super().update(model_id, data)

    async def perform_test_connection(self, config: dict[str, Any]) -> dict[str, Any]:
        """
        Perform the actual connection test logic.
        """
        driver_name = config["driver"].lower() if config["driver"] else ""
        password_to_use = config.get("password")

        try:
            driver = get_driver(driver_name, config)
            if driver:
                # Run connection test via registered driver
                result = await driver.test_connection()
                if result.get("status") == "error":
                    raise ValueError(result.get("message", "Connection test failed"))
                return result

            if driver_name in [
                "postgresql",
                "mysql",
                "mariadb",
                "trino",
                "mongodb",
                "mssql",
                "oracle",
            ]:
                # Database checks using SQLAlchemy
                db_driver_map = {
                    "postgresql": "postgresql+psycopg",
                    "mysql": "mysql+pymysql",
                    "mariadb": "mysql+pymysql",
                    "mssql": "mssql+pyodbc",
                    "oracle": "oracle+cx_oracle",
                    "trino": "trino",
                    "mongodb": "mongodb",
                }

                sa_driver = db_driver_map.get(driver_name, driver_name)

                url_kwargs = {
                    "username": config.get("login"),
                    "password": password_to_use,
                    "host": config.get("host"),
                    "port": config.get("port"),
                    "database": config.get("resource"),
                }

                url_kwargs = {k: v for k, v in url_kwargs.items() if v is not None}
                url = URL.create(drivername=sa_driver, **url_kwargs)

                if config.get("parameters"):
                    url = url.update_query_dict(config["parameters"])

                def _do_test_connection(url_to_test: URL) -> None:
                    engine = create_engine(url_to_test)
                    with engine.connect() as conn:
                        conn.execute(text("SELECT 1"))

                try:
                    await asyncio.to_thread(_do_test_connection, url)

                    return {
                        "status": "success",
                        "message": f"Successfully connected to {driver_name}",
                    }
                except Exception as e:
                    raise ValueError(f"Connection failed: {str(e)}")

            else:
                return {
                    "status": "unknown",
                    "message": f"Driver '{driver_name}' connection test not fully implemented, but saved.",
                }

        except Exception as e:
            # Re-raise as HTTPException with 422 to match test expectations
            raise HTTPException(
                status_code=422, detail=f"Connection test failed: {str(e)}"
            )


router = DataSourceService.router()


class TestConnectionRequest(BaseModel):
    # Allow overriding fields for testing "dirty" state, effectively optional
    driver: Optional[str] = None
    type: Optional[str] = None  # Alias for driver used in tests
    host: Optional[str] = None
    port: Optional[int] = None
    resource: Optional[str] = None
    login: Optional[str] = None
    password: Optional[str] = None
    api_key: Optional[str] = None  # Alias for password used in tests
    enable_ssl: Optional[bool] = None
    verify_ssl: Optional[bool] = None
    parameters: Optional[dict[str, Any]] = None

    def get_driver(self) -> Optional[str]:
        return self.driver or self.type

    def get_password(self) -> Optional[str]:
        return self.password or self.api_key


router = DataSourceService.router()


@router.post(
    f"{DataSourceService.service_path()}/_test-connection",
    tags=DataSourceService.path_tags(),
)
async def test_connection_no_id(
    data: TestConnectionRequest,
    svc: DataSourceService = Depends(DataSourceService.get_service),
):
    """
    Test connection to a data source without a saved record.
    """
    config = {
        "driver": data.get_driver(),
        "host": data.host,
        "port": data.port,
        "resource": data.resource,
        "login": data.login,
        "password": data.get_password(),
        "enable_ssl": data.enable_ssl,
        "verify_ssl": data.verify_ssl,
        "parameters": data.parameters or {},
    }
    return await svc.perform_test_connection(config)


@router.post(
    f"{DataSourceService.service_path()}/{{model_id}}/_test-connection",
    tags=DataSourceService.path_tags(),
)
async def test_connection(
    model_id: int,
    data: TestConnectionRequest = None,
    svc: DataSourceService = Depends(DataSourceService.get_service),
):
    """
    Test connection to a data source.
    Uses stored configuration, optionally overridden by provided data.
    """
    existing = await svc.get(model_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Data source not found")

    # Merge existing with overrides
    config = {
        "driver": existing.driver,
        "host": existing.host,
        "port": existing.port,
        "resource": existing.resource,
        "login": existing.login,
        "password": existing.password,
        "enable_ssl": existing.enable_ssl,
        "verify_ssl": existing.verify_ssl,
        "parameters": existing.parameters or {},
    }

    if data:
        overrides = data.model_dump(exclude_unset=True)
        # Handle special field mappings for overrides
        if data.type:
            overrides["driver"] = data.type
        if data.api_key:
            overrides["password"] = data.api_key

        for k, v in overrides.items():
            if v is not None:
                config[k] = v

    # Decrypt password if it's from DB and hasn't been overridden
    is_using_stored_password = not data or (
        data.password is None and data.api_key is None
    )

    if is_using_stored_password and existing.password:
        try:
            config["password"] = decrypt_password(existing.password)
        except EncryptionError:
            pass

    return await svc.perform_test_connection(config)
