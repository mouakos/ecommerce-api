"""User model for storing user information."""

from typing import TYPE_CHECKING, Optional

from sqlmodel import Field, Relationship

from app.models.common import TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.cart import Cart
    from app.models.order import Order


class User(UUIDMixin, TimestampMixin, table=True):
    """User model for storing user information."""

    __tablename__ = "users"
    email: str = Field(index=True, unique=True)
    hashed_password: str = Field(exclude=True)
    is_active: bool = Field(default=True)

    cart: Optional["Cart"] = Relationship(back_populates="user")
    orders: list["Order"] = Relationship(
        back_populates="user", sa_relationship_kwargs={"lazy": "selectin"}, cascade_delete=True
    )
