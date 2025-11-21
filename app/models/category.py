"""Category model with self-referencing parent-child relationships."""

from datetime import datetime
from typing import TYPE_CHECKING

from sqlmodel import Column, DateTime, Field, Relationship

from .common import TimestampMixin, UUIDMixin, utcnow

if TYPE_CHECKING:
    from app.models.product import Product  # noqa: F401


class Category(UUIDMixin, TimestampMixin, table=True):
    """Category model with self-referencing parent-child relationships."""

    __tablename__ = "categories"

    name: str = Field(index=True, unique=True)
    is_active: bool = Field(default=True)
    updated_at: datetime = Field(
        default_factory=utcnow,
        sa_column=Column(DateTime, default=utcnow, onupdate=utcnow, nullable=False),
    )

    products: list["Product"] = Relationship(
        back_populates="category", sa_relationship_kwargs={"lazy": "selectin"}, cascade_delete=True
    )
