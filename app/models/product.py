"""Product model definitions for the ecommerce API."""

from datetime import datetime
from typing import TYPE_CHECKING, Optional
from uuid import UUID

from sqlmodel import Column, DateTime, Field, Relationship, UniqueConstraint

from app.models.common import TimestampMixin, UUIDMixin, utcnow

if TYPE_CHECKING:
    from app.models.cart import CartItem
    from app.models.category import Category


class Product(UUIDMixin, TimestampMixin, table=True):
    """Product model for storing product information."""

    __tablename__ = "products"
    __table_args__ = (UniqueConstraint("name", "category_id"),)

    name: str
    description: str | None = None
    price: float
    stock: int
    updated_at: datetime = Field(
        default_factory=utcnow,
        sa_column=Column(DateTime, default=utcnow, onupdate=utcnow, nullable=False),
    )
    category_id: UUID = Field(foreign_key="categories.id", ondelete="CASCADE")

    category: Optional["Category"] = Relationship(back_populates="products")

    cart_items: list["CartItem"] = Relationship(
        back_populates="product", sa_relationship_kwargs={"lazy": "selectin"}, cascade_delete=True
    )
