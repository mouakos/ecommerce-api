"""Cart schema for managing shopping cart data in the application."""

from uuid import UUID

from pydantic import BaseModel, Field

from app.schemas.base import TimestampMixin, UUIDMixin


class CartReadItem(UUIDMixin):
    """Schema for reading cart items."""

    product_id: UUID
    quantity: int
    unit_price: float


class CartRead(UUIDMixin, TimestampMixin):
    """Schema for reading cart data."""

    user_id: UUID
    items: list[CartReadItem] = []


class CartItemCreate(BaseModel):
    """Schema for creating a new cart item."""

    product_id: UUID
    quantity: int = Field(default=1, ge=1)


class CartItemUpdate(BaseModel):
    """Schema for updating an existing cart item."""

    quantity: int | None = Field(default=None, ge=0)
