"""Models for Order and OrderItem."""

from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import Column, DateTime, UniqueConstraint
from sqlmodel import Field, Relationship

from app.core.enums import OrderStatus
from app.models.base import TimestampMixin, UUIDMixin
from app.utils.time import utcnow

if TYPE_CHECKING:
    from app.models.user import User


class Order(UUIDMixin, TimestampMixin, table=True):
    """Order model for storing order information."""

    __tablename__ = "orders"

    user_id: UUID = Field(foreign_key="users.id", index=True, ondelete="CASCADE")
    number: str = Field(index=True, unique=True)
    status: OrderStatus = Field(default=OrderStatus.PENDING)
    shipping_address_id: UUID = Field(foreign_key="addresses.id", index=True)
    billing_address_id: UUID = Field(foreign_key="addresses.id", index=True)
    total_amount: float
    updated_at: datetime = Field(
        default_factory=utcnow,
        sa_column=Column(DateTime, default=utcnow, onupdate=utcnow, nullable=False),
    )

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
