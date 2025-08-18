"""Configuration settings for the application using Pydantic."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Environment variables for the application."""

    # e.g. "postgresql+asyncpg://app:app@localhost:5432/ecom"
    DATABASE_URL: str = "sqlite+aiosqlite:///./ecom_dev.db"

    # auth
    SECRET_KEY: str = "change-me"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    JWT_ALGORITHM: str = "HS256"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


settings = Settings()
