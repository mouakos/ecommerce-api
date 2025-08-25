"""Schemas for user-related operations in the application."""

from pydantic import EmailStr, Field
from sqlmodel import SQLModel

from app.schemas.common import UUIDMixin


class UserCreate(SQLModel):
    """Schema for creating a new user."""

    email: EmailStr
    password: str = Field(..., min_length=6)


class UserRead(UUIDMixin):
    """Schema for reading user information."""

    email: str
    is_active: bool


class Token(SQLModel):
    """Schema for authentication token response."""

    access_token: str
    token_type: str = "bearer"
