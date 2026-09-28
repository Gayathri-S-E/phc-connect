from typing import List
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    APP_NAME: str = "Smart Health & Supply Chain Resilience"
    ENVIRONMENT: str = "development"
    DEBUG: bool = False
    PORT: int = 8000
    HOST: str = "0.0.0.0"

    # PostgreSQL Database
    DATABASE_URL: str = Field(
        default="postgresql+asyncpg://app_user:local_dev_secret_password@localhost:5432/smarthealth_db",
        description="Async database connection string",
    )
    DB_ECHO: bool = False
    DB_POOL_SIZE: int = 10
    DB_MAX_OVERFLOW: int = 5

    # JWT & Authentication
    JWT_SECRET: str = Field(
        default="local_dev_jwt_secret_key_must_be_overridden_in_production_environments_32_chars",
        description="Secret key for signing JWT tokens",
    )
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # CORS
    ALLOWED_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
    ]
    ALLOWED_HOSTS: List[str] = ["localhost", "127.0.0.1"]

    # Automatic monitoring (supply monitor + public-health analysis). Off by default so
    # tests and one-off scripts never start background work.
    ENABLE_BACKGROUND_JOBS: bool = False
    SUPPLY_MONITOR_INTERVAL_MINUTES: int = 60
    PUBLIC_HEALTH_ANALYSIS_INTERVAL_MINUTES: int = 24 * 60


settings = Settings()
