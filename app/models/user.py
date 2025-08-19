"""User model for storing user information."""

from typing import TYPE_CHECKING, Optional
from uuid import UUID, uuid4

from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from app.models.cart import Cart


class User(SQLModel, table=True):
    """User model for storing user information."""

    __tablename__ = "users"
    id: UUID = Field(default_factory=uuid4, primary_key=True, index=True)
    email: str = Field(index=True, unique=True)
    hashed_password: str = Field(exclude=True)
    is_active: bool = Field(default=True)

    cart: Optional["Cart"] = Relationship(back_populates="user")
