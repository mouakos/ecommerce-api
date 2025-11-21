"""Product model definitions for the ecommerce API."""

from datetime import datetime
from typing import TYPE_CHECKING, Optional
from uuid import UUID

from sqlmodel import Column, DateTime, Field, Relationship, UniqueConstraint

from app.models.base import TimestampMixin, UUIDMixin
from app.utils.time import utcnow

if TYPE_CHECKING:
    from app.models.cart import CartItem
    from app.models.category import Category
    from app.models.review import Review


class Product(UUIDMixin, TimestampMixin, table=True):
    """Product model for storing product information."""

    __tablename__ = "products"
    __table_args__ = (UniqueConstraint("name", "category_id"),)

    name: str
    description: str | None = None
    price: float
    stock: int
    is_available: bool = Field(default=True)
    updated_at: datetime = Field(
        default_factory=utcnow,
        sa_column=Column(DateTime, default=utcnow, onupdate=utcnow, nullable=False),
    )
    category_id: UUID = Field(foreign_key="categories.id", ondelete="CASCADE")

    category: Optional["Category"] = Relationship(back_populates="products")

    cart_items: list["CartItem"] = Relationship(
        back_populates="product", sa_relationship_kwargs={"lazy": "selectin"}, cascade_delete=True
    )
    reviews: list["Review"] = Relationship(
        back_populates="product", sa_relationship_kwargs={"lazy": "selectin"}, cascade_delete=True
    )
