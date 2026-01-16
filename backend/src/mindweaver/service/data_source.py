from . import NamedBase
from .base import ProjectScopedNamedBase, ProjectScopedService
from sqlalchemy import String, Text, Boolean
from sqlalchemy_utils import JSONType
from sqlmodel import Field
from typing import Any, Literal, Optional
from pydantic import BaseModel
from fastapi import HTTPException, Depends
from mindweaver.fw.exc import MindWeaverError
from mindweaver.crypto import encrypt_password, decrypt_password, EncryptionError
import httpx
from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL


class DataSource(ProjectScopedNamedBase, table=True):
    __tablename__ = "mw_datasource"

    description: Optional[str] = Field(
        default=None, sa_type=Text, sa_column_kwargs={"info": {"column_span": 2}}
    )
    driver: str = Field(
        sa_type=String(length=50),
        description="Source type / driver (e.g. web, postgresql, trino)",
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


class DataSourceService(ProjectScopedService[DataSource]):
    @classmethod
    def model_class(cls) -> type[DataSource]:
        return DataSource

    @classmethod
    def widgets(cls) -> dict[str, Any]:
        return {
            "password": {"type": "password"},
            "parameters": {"type": "key-value"},
        }

    def _encrypt_password_if_needed(self, data_dict: dict[str, Any]) -> None:
        """Encrypt password field if present and not empty."""
        password = data_dict.get("password")
        if password:
            if password == "__REDACTED__":
                # Should have been handled before, but just in case
                data_dict.pop("password")
            elif password == "__CLEAR__":
                data_dict["password"] = None
            else:
                try:
                    data_dict["password"] = encrypt_password(password)
                except EncryptionError as e:
                    raise HTTPException(
                        status_code=500, detail=f"Failed to encrypt password: {str(e)}"
                    )

    async def create(self, data: NamedBase) -> DataSource:
        data_dict = data.model_dump() if hasattr(data, "model_dump") else dict(data)
        self._encrypt_password_if_needed(data_dict)

        # Re-construct model with potentially modified dict (if we could, strictly)
        # But we are calling super().create(data).
        # We need to modify 'data' itself if it's a model instance, or pass dict to DB.
        # ProjectScopedService.create expects a NamedBase model.
        # Let's modify the attribute on 'data' directly if possible.
        if "password" in data_dict:
            if hasattr(data, "password"):
                setattr(data, "password", data_dict["password"])

        return await super().create(data)

    def post_process_model(self, model: DataSource) -> DataSource:
        if model.password:
            model.password = "__REDACTED__"
        return model

    async def update(self, model_id: int, data: NamedBase) -> DataSource:
        data_dict = (
            data.model_dump(exclude_unset=True)
            if hasattr(data, "model_dump")
            else dict(data)
        )

        existing = await self.get(model_id)
        if not existing:
            raise HTTPException(status_code=404, detail="Data source not found")

        # Handle password logic
        if "password" in data_dict:
            password = data_dict["password"]
            if password == "__REDACTED__":
                # Remove from update to keep existing
                pass
            elif password == "__CLEAR__":
                if hasattr(data, "password"):
                    setattr(data, "password", None)
            elif password:
                # Encrypt new password
                try:
                    encrypted = encrypt_password(password)
                    if hasattr(data, "password"):
                        setattr(data, "password", encrypted)
                except EncryptionError as e:
                    raise HTTPException(
                        status_code=500, detail=f"Failed to encrypt password: {str(e)}"
                    )
            else:
                # Empty string usually means clear or no change?
                # User config usually implies empty = no change or clear.
                # Let's assume empty string = None/Clear if it was passed explicitly?
                # Or just ignore? Standard practice regarding __REDACTED__ implies explicit clear is needed.
                # If user sends "", it might be intended as clearing.
                pass

        return await super().update(model_id, data)

    async def perform_test_connection(self, config: dict[str, Any]) -> dict[str, Any]:
        """
        Perform the actual connection test logic.
        """
        driver = config["driver"].lower() if config["driver"] else ""
        password_to_use = config.get("password")

        try:
            if driver == "web" or driver == "api" or driver == "web scraper":
                # Handle special parameter mappings from tests
                params = config.get("parameters", {})
                host = (
                    config.get("host")
                    or params.get("base_url")
                    or params.get("start_url")
                )

                if not host:
                    raise ValueError("Host/URL is required for Web/API source")

                # Parse host if it's a full URL
                if "://" in host:
                    from urllib.parse import urlparse

                    parsed = urlparse(host)
                    scheme = parsed.scheme
                    host_only = parsed.netloc
                    resource_only = parsed.path
                    if parsed.query:
                        resource_only += f"?{parsed.query}"
                else:
                    scheme = "https" if config.get("enable_ssl") else "http"
                    host_only = host
                    resource_only = config.get("resource") or ""

                base_url = f"{scheme}://{host_only}"
                if config.get("port") and ":" not in host_only:
                    base_url += f":{config['port']}"

                if resource_only:
                    if not resource_only.startswith("/"):
                        base_url += "/"
                    base_url += resource_only

                async with httpx.AsyncClient(
                    verify=config.get("verify_ssl", False)
                ) as client:
                    auth = None
                    if config.get("login") and password_to_use:
                        auth = (config["login"], password_to_use)
                    elif params.get("api_key"):
                        # Support api_key in parameters
                        pass  # TODO: handle as header?

                    resp = await client.get(
                        base_url, auth=auth, timeout=10.0, follow_redirects=True
                    )

                    return {
                        "status": "success",
                        "message": f"Connected to {base_url}. Status: {resp.status_code}",
                    }

            elif driver in [
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

                sa_driver = db_driver_map.get(driver, driver)

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

                try:
                    engine = create_engine(url)
                    with engine.connect() as conn:
                        if "trino" in driver:
                            conn.execute(text("SELECT 1"))
                        else:
                            conn.execute(text("SELECT 1"))

                    return {
                        "status": "success",
                        "message": f"Successfully connected to {driver}",
                    }
                except Exception as e:
                    raise ValueError(f"Connection failed: {str(e)}")

            else:
                return {
                    "status": "unknown",
                    "message": f"Driver '{driver}' connection test not fully implemented, but saved.",
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
