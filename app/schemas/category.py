"""Category schema definitions for creating, reading, and updating categories."""

from pydantic import BaseModel, Field

from app.schemas.base import TimestampMixin, UUIDMixin


class CategoryCreate(BaseModel):
    """Category create model."""

    name: str = Field(..., min_length=2, max_length=50, description="Name of the category")
    is_active: bool = Field(True, description="Whether the category is active")


class CategoryRead(CategoryCreate, UUIDMixin, TimestampMixin):
    """Category read model."""

    pass


class CategoryUpdate(BaseModel):
    """Category update model."""

    name: str | None = Field(None, min_length=2, max_length=50, description="Name of the category")
    is_active: bool | None = Field(None, description="Set active status of the category")
