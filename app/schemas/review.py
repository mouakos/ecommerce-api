"""Schemas for product reviews."""

from uuid import UUID

from pydantic import BaseModel, Field

from app.schemas.base import TimestampMixin, UUIDMixin


class ReviewCreate(BaseModel):
    """Schema for creating a review."""

    rating: int = Field(..., ge=1, le=5, description="Star rating 1-5")
    comment: str | None = Field(None, max_length=1000, description="Optional review text")


class ReviewUpdate(BaseModel):
    """Schema for updating a review (author or admin)."""

    rating: int | None = Field(None, ge=1, le=5)
    comment: str | None = Field(None, max_length=1000)


class ReviewAdminUpdate(BaseModel):
    """Schema for moderating visibility (admin only)."""

    is_visible: bool


class ReviewRead(ReviewCreate, UUIDMixin, TimestampMixin):
    """Schema for reading review data."""

    product_id: UUID
    user_id: UUID
    is_visible: bool


class AverageReview(BaseModel):
    """Schema for average review data."""

    average_rating: float | None
    review_count: int
