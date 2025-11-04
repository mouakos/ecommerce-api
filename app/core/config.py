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
    # auth
    secret_key: str = Field(
        default="",
        description="Secret key for JWT signing",
        alias="SECRET_KEY",
    )
    access_token_expire_minutes: int = Field(
        default=60,
        description="Access token expiration time in minutes",
        alias="ACCESS_TOKEN_EXPIRE_MINUTES",
    )
    jwt_algorithm: str = Field(
        default="HS256", description="JWT signing algorithm", alias="JWT_ALGORITHM"
    )

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


settings = Settings()
