"""User model for storing user information."""

from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlmodel import Column, DateTime, Field, Relationship

from app.models.base import TimestampMixin, UUIDMixin
from app.utils.time import utcnow

if TYPE_CHECKING:  # pragma: no cover
    from app.models.address import Address
    from app.models.cart import Cart
    from app.models.order import Order
    from app.models.review import Review


class User(UUIDMixin, TimestampMixin, table=True):
    """User model for storing user information."""

    __tablename__ = "users"
    email: str = Field(index=True, unique=True)
    hashed_password: str = Field(exclude=True)
    is_active: bool = Field(default=True)
    is_verified: bool = Field(default=False)
    role: str = Field(default="user")
    first_name: str | None = None
    last_name: str | None = None
    phone_number: str | None = None
    updated_at: datetime = Field(
        default_factory=utcnow,
        sa_column=Column(DateTime, default=utcnow, onupdate=utcnow, nullable=False),
    )

    cart: Optional["Cart"] = Relationship(back_populates="user")
    orders: list["Order"] = Relationship(
        back_populates="user", sa_relationship_kwargs={"lazy": "selectin"}, cascade_delete=True
    )
    reviews: list["Review"] = Relationship(
        back_populates="user", sa_relationship_kwargs={"lazy": "selectin"}, cascade_delete=True
    )
    addresses: list["Address"] = Relationship(
        back_populates="user", sa_relationship_kwargs={"lazy": "selectin"}, cascade_delete=True
    )
