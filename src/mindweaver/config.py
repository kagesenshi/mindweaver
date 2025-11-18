from pydantic_settings import BaseSettings, SettingsConfigDict
from urllib.parse import quote as urlquote
import logging

class Settings(BaseSettings):
    db_type: str = 'postgresql'
    db_driver: str = 'postgresql+psycopg2'
    db_async_driver: str = 'postgresql+asyncpg'
    db_host: str = 'localhost'
    db_port: int = 5432
    db_name: str = 'mindweaver'
    db_user: str | None = None
    db_pass: str | None = None
    model_config  = SettingsConfigDict(env_file='.env', env_prefix='mindweaver_', extra='allow')

    @property
    def db_uri(self):
        if self.db_user and self.db_pass:
            return f'{self.db_driver}://{urlquote(self.db_user)}:{urlquote(self.db_pass)}@{self.db_host}:{self.db_port}/{self.db_name}'
        return f'{self.db_driver}://{self.db_host}:{self.db_port}/{self.db_name}'
    
    @property
    def db_async_uri(self):
        if self.db_user and self.db_pass:
            return f'{self.db_async_driver}://{urlquote(self.db_user)}:{urlquote(self.db_pass)}@{self.db_host}:{self.db_port}/{self.db_name}'
        return f'{self.db_async_driver}://{self.db_host}:{self.db_port}/{self.db_name}'

logger = logging.getLogger('mindweaver')
settings = Settings()