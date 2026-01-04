from pydantic_settings import BaseSettings, SettingsConfigDict
from urllib.parse import quote as urlquote
import logging


class Settings(BaseSettings):
    db_type: str = "postgresql"
    db_driver: str = "postgresql+psycopg2"
    db_async_driver: str = "postgresql+asyncpg"
    db_host: str = "localhost"
    db_port: int = 5432
    db_name: str = "mindweaver"
    db_user: str | None = None
    db_pass: str | None = None
    timezone: str = "Asia/Kuala_Lumpur"
    enable_db_reset: bool = False
    enable_test_views: bool = False
    fernet_key: str | None = None
    jwt_secret: str = "unsafe-secret-key-change-me"

    experimental_data_source: bool = False
    experimental_knowledge_db: bool = False
    experimental_s3_storage: bool = False
    experimental_ingestion: bool = False

    oidc_issuer: str | None = None
    oidc_client_id: str | None = None
    oidc_client_secret: str | None = None

    model_config = SettingsConfigDict(
        env_file=".env", env_prefix="mindweaver_", extra="allow"
    )

    @property
    def db_uri(self):
        login = None
        if self.db_user:
            login = urlquote(self.db_user)
            if self.db_pass:
                login = f"{login}:{urlquote(self.db_pass)}"
        if login:
            return f"{self.db_driver}://{login}@{self.db_host}:{self.db_port}/{self.db_name}"
        return f"{self.db_driver}://{self.db_host}:{self.db_port}/{self.db_name}"

    @property
    def db_async_uri(self):
        login = None
        if self.db_user:
            login = urlquote(self.db_user)
            if self.db_pass:
                login = f"{login}:{urlquote(self.db_pass)}"
        if login:
            return f"{self.db_async_driver}://{login}@{self.db_host}:{self.db_port}/{self.db_name}"
        return f"{self.db_async_driver}://{self.db_host}:{self.db_port}/{self.db_name}"


logger = logging.getLogger("mindweaver")
settings = Settings()
