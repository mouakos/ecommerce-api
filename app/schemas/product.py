"""Product schema definitions for the ecommerce API."""

from uuid import UUID

from pydantic import BaseModel, Field

from app.schemas.base import TimestampMixin, UUIDMixin


class ProductCreate(BaseModel):
    """Schema for creating a new product."""

    name: str = Field(..., min_length=2, max_length=100, description="Product name")
    description: str | None = Field(None, max_length=500, description="Short product description")
    price: float = Field(..., ge=0, description="Product price")
    stock: int = Field(..., ge=0, description="Units available in stock")
    category_id: UUID = Field(..., description="Category ID this product belongs to")


class ProductRead(ProductCreate, UUIDMixin, TimestampMixin):
    """Schema for reading product information."""

    pass


class ProductUpdate(BaseModel):
    """Schema for updating an existing product."""

    name: str | None = Field(None, max_length=100, description="Product name")
    description: str | None = Field(None, max_length=500, description="Short product description")
    price: float | None = Field(None, ge=0, description="Product price")
    stock: int | None = Field(None, ge=0, description="Units available in stock")
    category_id: UUID | None = Field(None, description="Category ID this product belongs to")
