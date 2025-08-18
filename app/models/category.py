"""Category model with self-referencing parent-child relationships."""

from typing import TYPE_CHECKING

from sqlmodel import Field, Relationship

from .common import TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.product import Product  # noqa: F401


class Category(UUIDMixin, TimestampMixin, table=True):
    """Category model with self-referencing parent-child relationships."""

    __tablename__ = "categories"

    name: str = Field(index=True, unique=True, nullable=False)

    products: list["Product"] = Relationship(
        back_populates="category", sa_relationship_kwargs={"lazy": "selectin"}, passive_deletes=True
    )
