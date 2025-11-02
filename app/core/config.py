"""Configuration settings for the application using Pydantic."""

from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlmodel import Field


class Settings(BaseSettings):
    """Environment variables for the application."""

    # database
    DATABASE_URL: str = Field(default="", description="Database connection URL")

    # auth
    SECRET_KEY: str = Field(default="", description="Secret key for JWT signing")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(
        default=60, description="Access token expiration time in minutes"
    )
    JWT_ALGORITHM: str = Field(default="HS256", description="JWT signing algorithm")

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


settings = Settings()
