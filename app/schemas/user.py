"""Schemas for user-related operations in the application."""

from pydantic import BaseModel, EmailStr, Field

from app.schemas.base import TimestampMixin, UUIDMixin


class UserCreate(BaseModel):
    """Schema for creating a new user."""

    email: EmailStr
    password: str = Field(..., min_length=6)


class UserLogin(UserCreate):
    """Schema for user login."""

    pass


class UserRead(UUIDMixin, TimestampMixin):
    """Schema for reading user information."""

    email: str
    is_active: bool
    is_verified: bool
    role: str


class Token(BaseModel):
    """Schema for authentication token response."""

    access_token: str
    refresh_token: str | None = None
    token_type: str = "bearer"
