"""Category schema definitions for creating, reading, and updating categories."""

from uuid import UUID

from pydantic import BaseModel, Field


class CategoryCreate(BaseModel):
    """Category create model."""

    name: str = Field(..., min_length=2, max_length=50)


class CategoryRead(BaseModel):
    """Category read model."""

    id: UUID
    name: str


class CategoryUpdate(BaseModel):
    """Category update model."""

    name: str | None = None
