"""Cart and CartItem models for managing shopping cart functionality in an e-commerce application."""

from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import Column, UniqueConstraint
from sqlmodel import DateTime, Field, Relationship

from app.models.common import TimestampMixin, UUIDMixin, utcnow

if TYPE_CHECKING:
    from app.models.product import Product
    from app.models.user import User


class Cart(UUIDMixin, TimestampMixin, table=True):
    """Cart model for storing shopping cart information."""

    __tablename__ = "carts"
    user_id: UUID = Field(foreign_key="users.id", index=True, nullable=False, ondelete="CASCADE")
    items: list["CartItem"] = Relationship(
        back_populates="cart", sa_relationship_kwargs={"lazy": "selectin"}, cascade_delete=True
    )
    updated_at: datetime = Field(
        default_factory=utcnow,
        sa_column=Column(DateTime, default=utcnow, onupdate=utcnow, nullable=False),
    )

    user: "User" = Relationship(back_populates="cart")


class CartItem(UUIDMixin, TimestampMixin, table=True):
    """Cart item model for storing items in a shopping cart."""

    __tablename__ = "cart_items"
    __table_args__ = (UniqueConstraint("cart_id", "product_id"),)  # one product per cart

    cart_id: UUID = Field(foreign_key="carts.id", index=True, ondelete="CASCADE")
    product_id: UUID = Field(foreign_key="products.id", index=True, ondelete="CASCADE")
    quantity: int
    # snapshot price (so changes to Product.price don’t affect existing items)
    unit_price: float
    updated_at: datetime = Field(
        default_factory=utcnow,
        sa_column=Column(DateTime, default=utcnow, onupdate=utcnow, nullable=False),
    )

    cart: "Cart" = Relationship(back_populates="items")
    product: "Product" = Relationship(back_populates="cart_items")
