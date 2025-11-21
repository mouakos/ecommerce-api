"""Address schemas."""

from uuid import UUID

from pydantic import BaseModel

from app.schemas.base import TimestampMixin, UUIDMixin


class AddressCreate(BaseModel):
    """Schema for creating a new address."""

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


class AddressRead(AddressCreate, UUIDMixin, TimestampMixin):
    """Schema for reading address information."""

    user_id: UUID


class AddressUpdate(BaseModel):
    """Partial update payload for an address (no default flags)."""

    first_name: str | None = None
    last_name: str | None = None
    company: str | None = None
    line1: str | None = None
    line2: str | None = None
    city: str | None = None
    state: str | None = None
    postal_code: str | None = None
    country: str | None = None
    phone_number: str | None = None
