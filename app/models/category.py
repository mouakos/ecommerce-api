"""Category model with self-referencing parent-child relationships."""

from sqlmodel import Field

from .common import TimestampMixin, UUIDMixin


class Category(UUIDMixin, TimestampMixin, table=True):
    """Category model with self-referencing parent-child relationships."""

    __tablename__ = "categories"

    name: str = Field(index=True, unique=True, nullable=False)
