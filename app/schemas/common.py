"""Common Pydantic Schemas."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class TimestampMixin(BaseModel):
    """Mixin to add created_at and updated_at timestamps."""

    created_at: datetime

    updated_at: datetime


class UUIDMixin(BaseModel):
    """Mixin to add a UUID primary key."""

    id: UUID
