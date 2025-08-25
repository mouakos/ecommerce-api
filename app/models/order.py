"""Models for Order and OrderItem."""

from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import UniqueConstraint
from sqlmodel import Field, Relationship

from app.models.common import TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.user import User


class Order(UUIDMixin, TimestampMixin, table=True):
    """Order model for storing order information."""

    __tablename__ = "orders"

    user_id: UUID = Field(foreign_key="users.id", index=True, ondelete="CASCADE")
    number: str = Field(index=True, unique=True, description="Public order number")
    status: str = Field(default="created")  # created, paid, cancelled
    total_amount: float

    items: list["OrderItem"] = Relationship(
        back_populates="order", sa_relationship_kwargs={"lazy": "selectin"}, cascade_delete=True
    )

    user: "User" = Relationship(back_populates="orders")


class OrderItem(UUIDMixin, table=True):
    """Order item model for storing items in an order."""

    __tablename__ = "order_items"
    __table_args__ = (UniqueConstraint("order_id", "product_id"),)

    order_id: UUID = Field(foreign_key="orders.id", index=True, ondelete="CASCADE")
    product_id: UUID = Field(foreign_key="products.id", index=True, ondelete="CASCADE")
    quantity: int
    unit_price: float

    order: "Order" = Relationship(back_populates="items")
