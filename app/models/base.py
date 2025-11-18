"""Reusable SQLModel mixins.

These mixins depend on helpers from app.shared.time but avoid importing broader model modules.
"""

from datetime import datetime
from uuid import UUID, uuid4

from sqlmodel import Field, SQLModel

from app.utils.time import utcnow


class TimestampMixin(SQLModel):
    """Mixin adding created_at timestamp (auto-set on insert)."""

    created_at: datetime = Field(default_factory=utcnow)


class UUIDMixin(SQLModel):
    """Mixin adding UUID primary key field 'id'."""

    id: UUID = Field(default_factory=uuid4, primary_key=True)
