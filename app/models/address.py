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
    label: str | None = Field(default=None, description="Short label like 'Home' or 'Office'")
    first_name: str | None = None
    last_name: str | None = None
    company: str | None = None
    line1: str = Field(description="Primary street address line")
    line2: str | None = Field(default=None, description="Secondary address line")
    city: str = Field(description="City or locality")
    state: str | None = Field(default=None, description="State/Province/Region")
    postal_code: str = Field(description="Postal or ZIP code")
    country: str = Field(description="ISO 3166-1 alpha-2 country code")
    phone_number: str | None = None
    is_default_shipping: bool = Field(default=False)
    is_default_billing: bool = Field(default=False)
    updated_at: datetime = Field(
        default_factory=utcnow,
        sa_column=Column(DateTime, default=utcnow, onupdate=utcnow, nullable=False),
    )

    user: Optional["User"] = Relationship(back_populates="addresses")
