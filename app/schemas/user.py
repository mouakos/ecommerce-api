"""Schemas for user-related operations in the application."""

from uuid import UUID

from pydantic import EmailStr, Field
from sqlmodel import SQLModel


class UserCreate(SQLModel):
    """Schema for creating a new user."""

    email: EmailStr
    password: str = Field(..., min_length=6)


class UserRead(SQLModel):
    """Schema for reading user information."""

    id: UUID
    email: str
    is_active: bool


class Token(SQLModel):
    """Schema for authentication token response."""

    access_token: str
    token_type: str = "bearer"
