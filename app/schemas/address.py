"""Address schemas."""

from uuid import UUID

from pydantic import BaseModel, field_validator

from app.schemas.base import TimestampMixin, UUIDMixin


class AddressBase(BaseModel):
    """Shared address field definitions."""

    label: str | None = None
    first_name: str | None = None
    last_name: str | None = None
    company: str | None = None
    line1: str
    line2: str | None = None
    city: str
    state: str | None = None
    postal_code: str
    country: str
    phone_number: str | None = None

    @field_validator("country")
    @classmethod
    def validate_country(cls, v: str) -> str:
        """Ensure country is a two-letter ISO code."""
        v2 = v.upper()
        if len(v2) != 2:
            raise ValueError("country must be 2-letter ISO code")
        return v2


class AddressCreate(AddressBase):
    """Payload for creating a new address."""

    set_default_shipping: bool | None = False
    set_default_billing: bool | None = False


class AddressUpdate(BaseModel):
    """Partial update payload for an address."""

    label: str | None = None
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
    set_default_shipping: bool | None = None
    set_default_billing: bool | None = None


class AddressRead(UUIDMixin, TimestampMixin):
    """Read model for returning address data."""

    user_id: UUID
    label: str | None = None
    first_name: str | None = None
    last_name: str | None = None
    company: str | None = None
    line1: str
    line2: str | None = None
    city: str
    state: str | None = None
    postal_code: str
    country: str
    phone_number: str | None = None
    is_default_shipping: bool
    is_default_billing: bool
