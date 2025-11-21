from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Frontend application settings."""
    
    model_config = SettingsConfigDict(
        env_prefix="MINDWEAVER_FE_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )
    
    api_base_url: str = "http://localhost:5000"
    api_timeout: int = 30


settings = Settings()
