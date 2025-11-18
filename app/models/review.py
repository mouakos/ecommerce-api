"""Review model for product reviews."""

from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID

from sqlmodel import Column, DateTime, Field, Relationship, UniqueConstraint

from app.models.base import TimestampMixin, UUIDMixin
from app.utils.time import utcnow

if TYPE_CHECKING:
    from app.models.product import Product
    from app.models.user import User


class Review(UUIDMixin, TimestampMixin, table=True):
    """Review model representing a user's rating & comment for a product."""

    __tablename__ = "reviews"
    __table_args__ = (UniqueConstraint("product_id", "user_id"),)

    product_id: UUID = Field(foreign_key="products.id", ondelete="CASCADE")
    user_id: UUID = Field(foreign_key="users.id", ondelete="CASCADE")
    rating: int
    comment: str | None = None
    is_visible: bool = True
    updated_at: datetime = Field(
        default_factory=utcnow,
        sa_column=Column(DateTime, default=utcnow, onupdate=utcnow, nullable=False),
    )

    product: "Product" = Relationship(back_populates="reviews")
    user: "User" = Relationship(back_populates="reviews")
