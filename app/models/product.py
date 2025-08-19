"""Product model definitions for the ecommerce API."""

from typing import TYPE_CHECKING, Optional
from uuid import UUID

from sqlmodel import Field, Relationship

from app.models.common import TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.cart import CartItem
    from app.models.category import Category


class Product(UUIDMixin, TimestampMixin, table=True):
    """Product model for storing product information."""

    __tablename__ = "products"

    name: str = Field()
    description: str | None = None
    price: float
    stock: int
    category_id: UUID = Field(foreign_key="categories.id", nullable=False, ondelete="CASCADE")

    category: Optional["Category"] = Relationship(back_populates="products")

    cart_items: list["CartItem"] = Relationship(
        back_populates="product", sa_relationship_kwargs={"lazy": "selectin"}, passive_deletes=True
    )
