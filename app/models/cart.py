"""Cart and CartItem models for managing shopping cart functionality in an e-commerce application."""

from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import UniqueConstraint
from sqlmodel import Field, Relationship, SQLModel

from app.models.common import TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.product import Product
    from app.models.user import User


class Cart(UUIDMixin, TimestampMixin, table=True):
    """Cart model for storing shopping cart information."""

    __tablename__ = "carts"
    user_id: UUID = Field(foreign_key="users.id", index=True, nullable=False, ondelete="CASCADE")
    items: list["CartItem"] = Relationship(
        back_populates="cart", sa_relationship_kwargs={"lazy": "selectin"}, passive_deletes=True
    )

    user: "User" = Relationship(back_populates="cart")


class CartItem(SQLModel, table=True):
    """Cart item model for storing items in a shopping cart."""

    __tablename__ = "cart_items"
    __table_args__ = (UniqueConstraint("cart_id", "product_id"),)  # one product per cart

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    cart_id: UUID = Field(foreign_key="carts.id", index=True, ondelete="CASCADE")
    product_id: UUID = Field(foreign_key="products.id", index=True, ondelete="CASCADE")
    quantity: int
    # snapshot price (so changes to Product.price don’t affect existing items)
    unit_price: float

    cart: "Cart" = Relationship(back_populates="items")
    product: "Product" = Relationship(back_populates="cart_items")
