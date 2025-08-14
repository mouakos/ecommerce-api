"""Common mixins for SQLModel models.

These mixins can be used to add common fields like timestamps and UUIDs to your models.
"""

from datetime import datetime
from uuid import UUID, uuid4

from sqlmodel import Field, SQLModel


class TimestampMixin(SQLModel):
    """Mixin to add created_at and updated_at timestamps."""

    created_at: datetime | None = Field(default_factory=datetime.utcnow, nullable=False)
    updated_at: datetime | None = Field(default_factory=datetime.utcnow, nullable=False)


class UUIDMixin(SQLModel):
    """Mixin to add a UUID primary key."""

    id: UUID = Field(default_factory=uuid4, primary_key=True, index=True)
