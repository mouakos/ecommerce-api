"""User model for storing user information."""

from uuid import UUID, uuid4

from sqlmodel import Field, SQLModel


class User(SQLModel, table=True):
    """User model for storing user information."""

    __tablename__ = "users"
    id: UUID = Field(default_factory=uuid4, primary_key=True, index=True)
    email: str = Field(index=True, unique=True)
    hashed_password: str = Field(exclude=True)
    is_active: bool = Field(default=True)
