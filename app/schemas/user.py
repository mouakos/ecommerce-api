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
    first_name: str | None = None
    last_name: str | None = None
    phone_number: str | None = None


class UserUpdate(BaseModel):
    """Schema for updating user information."""

    first_name: str | None = None
    last_name: str | None = None
    phone_number: str | None = None


class UserRoleUpdate(BaseModel):
    """Schema for updating a user's role."""

    role: str


class Token(BaseModel):
    """Schema for authentication token response."""

    access_token: str
    refresh_token: str | None = None
    token_type: str = "bearer"


class EmailSchema(BaseModel):
    """Schema for email operations."""

    email: EmailStr


class PasswordResetConfirm(BaseModel):
    """Schema for confirming a password reset."""

    new_password: str = Field(..., min_length=6)
    confirm_new_password: str
