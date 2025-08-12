"""Configuration settings for the application using Pydantic."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Environment variables for the application."""

    APP_NAME: str = "Ecommerce API"
    # e.g. "postgresql+asyncpg://app:app@localhost:5432/ecom"
    DATABASE_URL: str = ""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


settings = Settings()
