"""Configuration settings for the application using Pydantic."""

import secrets

from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlmodel import Field


class Settings(BaseSettings):
    """Environment variables for the application."""

    # database
    database_url: str = Field(
        "sqlite+aiosqlite:///./dev.db",
        description=(
            "Database connection URL. Defaults to a local file-based SQLite for fast dev iteration. "
            "Override with Postgres (e.g. postgresql+asyncpg://user:pass@localhost:5432/db) in .env or environment."
        ),
        alias="DATABASE_URL",
    )

    # auth
    secret_key: str = Field(
        default_factory=lambda: secrets.token_urlsafe(32),
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
