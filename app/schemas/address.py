"""Address schemas."""

from uuid import UUID

from pydantic import BaseModel

from app.schemas.base import TimestampMixin, UUIDMixin


class AddressBase(BaseModel):
    """Shared address field definitions."""

    first_name: str | None = None
    last_name: str | None = None
    company: str | None = None
    street: str
    city: str
    state: str | None = None
    postal_code: str
    country: str
    phone_number: str | None = None


class AddressCreate(AddressBase):
    """Payload for creating a new address."""

    set_default_shipping: bool | None = False
    set_default_billing: bool | None = False


class AddressUpdate(BaseModel):
    """Partial update payload for an address."""

    first_name: str | None = None
    last_name: str | None = None
    company: str | None = None
    street: str | None = None
    city: str | None = None
    state: str | None = None
    postal_code: str | None = None
    country: str | None = None
    phone_number: str | None = None
    set_default_shipping: bool | None = None
    set_default_billing: bool | None = None


class AddressRead(UUIDMixin, TimestampMixin):
    """Read model for returning address data."""

    user_id: UUID
    first_name: str | None = None
    last_name: str | None = None
    company: str | None = None
    street: str
    city: str
    state: str | None = None
    postal_code: str
    country: str
    phone_number: str | None = None
    is_default_shipping: bool
    is_default_billing: bool
