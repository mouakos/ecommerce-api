"""Common Pydantic Schemas."""

from datetime import datetime
from typing import TypeVar
from uuid import UUID

from pydantic import BaseModel
from sqlmodel import SQLModel


class TimestampMixin(BaseModel):
    """Mixin to add created_at and updated_at timestamps."""

    created_at: datetime

    updated_at: datetime


class UUIDMixin(BaseModel):
    """Mixin to add a UUID primary key."""

    id: UUID


T = TypeVar("T")


class Page[T](SQLModel):
    """Pagination information."""

    items: list[T]
    total: int
    limit: int
    offset: int
