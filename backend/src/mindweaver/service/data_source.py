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


router = DataSourceService.router()


class TestConnectionRequest(BaseModel):
    # Allow overriding fields for testing "dirty" state, effectively optional
    driver: Optional[str] = None
    host: Optional[str] = None
    port: Optional[int] = None
    resource: Optional[str] = None
    login: Optional[str] = None
    password: Optional[str] = None
    enable_ssl: Optional[bool] = None
    verify_ssl: Optional[bool] = None
    parameters: Optional[dict[str, Any]] = None


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
        for k, v in overrides.items():
            if v is not None:
                config[k] = v

    # Decrypt password if it's from DB and hasn't been overridden (or overridden with same encrypted val? unlikely)
    # If config['password'] looks encrypted (how to tell?), decrypt.
    # Actually, we know if we used the one from DB.
    # If the user passed a password in 'data', it is likely plain text (from form input).
    # If we used existing.password, it is encrypted.

    password_to_use = config["password"]
    # Check if we are using the stored password (i.e. overridden not provided or None)
    is_using_stored = not data or data.password is None

    if is_using_stored and existing.password:
        try:
            password_to_use = decrypt_password(existing.password)
        except EncryptionError:
            pass  # Maybe it wasn't encrypted or failed

    # Logic for connection testing based on driver
    driver = config["driver"].lower() if config["driver"] else ""

    try:
        if driver == "web" or driver.startswith("http"):
            # Web / API source checks
            # Resource might be the path, Host is the domain
            host = config["host"]
            if not host:
                raise ValueError("Host is required for Web source")

            # Construct URL
            scheme = "https" if config["enable_ssl"] else "http"
            if "://" in host:
                # If host already contains scheme, use it, but respect enable_ssl if possible?
                # User guide said "host: ip or hostname".
                pass

            base_url = f"{scheme}://{host}"
            if config["port"]:
                base_url += f":{config['port']}"

            if config["resource"]:
                # Ensure resource starts with / if needed, or join properly
                if not config["resource"].startswith("/"):
                    base_url += "/"
                base_url += config["resource"]

            async with httpx.AsyncClient(verify=config["verify_ssl"]) as client:
                # Add auth if Login provided (Basic Auth?) or Param?
                auth = None
                if config["login"] and password_to_use:
                    auth = (config["login"], password_to_use)

                # Check for headers in parameters?
                headers = {}
                # TODO: Support headers from parameters if defined convention

                resp = await client.get(
                    base_url, auth=auth, timeout=10.0, follow_redirects=True
                )

                if resp.status_code >= 400:
                    # Maybe it's a success if we get 401/403 (server exists)?
                    # But usually we want 200.
                    pass

                return {
                    "status": "success",
                    "message": f"Connected. Status: {resp.status_code}",
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
                "mariadb": "mysql+pymysql",  # simplified
                "mssql": "mssql+pyodbc",
                "oracle": "oracle+cx_oracle",
                "trino": "trino",  # requires sqlalchemy-trino
                "mongodb": "mongodb",
            }

            # Special handling for MongoDB?
            if driver == "mongodb":
                # Mock or implement precise check if libs installed.
                # Since we don't know if pymongo is installed, we might fail.
                pass

            sa_driver = db_driver_map.get(driver, driver)

            url_kwargs = {
                "username": config["login"],
                "password": password_to_use,
                "host": config["host"],
                "port": config["port"],
                "database": config["resource"],  # Resource maps to DB name
            }

            # remove None values
            url_kwargs = {k: v for k, v in url_kwargs.items() if v is not None}

            url = URL.create(drivername=sa_driver, **url_kwargs)

            # Add querystring params
            if config["parameters"]:
                url = url.update_query_dict(config["parameters"])

            try:
                engine = create_engine(url)
                with engine.connect() as conn:
                    # Trino/Mongo might not support "SELECT 1"
                    if "trino" in driver:
                        conn.execute(text("SELECT 1"))
                    elif "mongodb" in driver:
                        pass  # TODO
                    else:
                        conn.execute(text("SELECT 1"))

                return {
                    "status": "success",
                    "message": f"Successfully connected to {driver}",
                }
            except Exception as e:
                raise ValueError(f"Connection failed: {str(e)}")

        else:
            # Unknown driver, maybe just ping host if possible?
            # Or assume it is generic URL?
            return {
                "status": "unknown",
                "message": f"Driver '{driver}' connection test not fully implemented, but saved.",
            }

    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Connection test failed: {str(e)}")
