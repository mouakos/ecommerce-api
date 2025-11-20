"""Schemas for order-related data models."""

from uuid import UUID

from pydantic import BaseModel

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
    shipping_address_id: UUID | None = None
    billing_address_id: UUID | None = None


class OrderStatusUpdate(BaseModel):
    """Schema for updating order status."""

    status: OrderStatus


class OrderCheckout(BaseModel):
    """Schema for initiating a checkout with optional address references."""

    shipping_address_id: UUID | None = None
    billing_address_id: UUID | None = None
