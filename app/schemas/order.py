"""Schemas for order-related data models."""

from uuid import UUID

from app.schemas.common import TimestampMixin, UUIDMixin


class OrderItemRead(UUIDMixin):
    """Schema for reading order item information."""

    product_id: UUID
    quantity: int
    unit_price: float


class OrderRead(UUIDMixin, TimestampMixin):
    """Schema for reading order information."""

    number: str
    status: str
    items: list[OrderItemRead]
    total_amount: float
