"""Configuration settings for the application using Pydantic."""

from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlmodel import Field


class Settings(BaseSettings):
    """Environment variables for the application."""

    # database
    database_url: str = Field(
        default="", alias="DATABASE_URL", description="Database connection URL"
    )
    test_database_url: str = Field(
        default="sqlite+aiosqlite:///:memory:",
        alias="TEST_DATABASE_URL",
        description="Test database connection URL",
    )
    # redis
    redis_url: str = Field(
        default="redis://redis:6379/0",
        description="Redis connection URL",
        alias="REDIS_URL",
    )
    # auth
    secret_key: str = Field(
        default="",
        description="Secret key for JWT signing",
        alias="SECRET_KEY",
    )
    access_token_expire_minutes: int = Field(
        default=15,
        description="Access token expiration time in minutes",
        alias="ACCESS_TOKEN_EXPIRE_MINUTES",
    )
    refresh_token_expire_days: int = Field(
        default=7,
        description="Refresh token expiration time in days",
        alias="REFRESH_TOKEN_EXPIRE_DAYS",
    )
    jwt_algorithm: str = Field(
        default="HS256", description="JWT signing algorithm", alias="JWT_ALGORITHM"
    )

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


settings = Settings()
