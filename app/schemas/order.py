"""Schemas for order-related data models."""

from uuid import UUID

from app.core.enums import OrderStatus
from app.schemas.base import TimestampMixin, UUIDMixin


class OrderItemRead(UUIDMixin):
    """Schema for reading order item information."""

    product_id: UUID
    quantity: int
    unit_price: float


class OrderRead(UUIDMixin, TimestampMixin):
    """Schema for reading order information."""

    number: str
    status: OrderStatus
    items: list[OrderItemRead]
    total_amount: float
