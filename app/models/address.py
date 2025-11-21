"""Address model for user addresses (shipping/billing)."""

from datetime import datetime
from typing import TYPE_CHECKING, Optional
from uuid import UUID

from sqlmodel import Column, DateTime, Field, Relationship

from app.models.base import TimestampMixin, UUIDMixin
from app.utils.time import utcnow

if TYPE_CHECKING:  # pragma: no cover
    from app.models.user import User


class Address(UUIDMixin, TimestampMixin, table=True):
    """Address model for storing user address information."""

    __tablename__ = "addresses"
    user_id: UUID = Field(index=True, foreign_key="users.id", nullable=False)
    first_name: str | None = None
    last_name: str | None = None
    company: str | None = None
    line1: str
    line2: str | None = None
    city: str
    state: str
    postal_code: str
    country: str
    phone_number: str | None = None
    updated_at: datetime = Field(
        default_factory=utcnow,
        sa_column=Column(DateTime, default=utcnow, onupdate=utcnow, nullable=False),
    )

    user: Optional["User"] = Relationship(back_populates="addresses")
