"""add shipping and billing address columns to orders

Revision ID: 2a4d3b9c2e10
Revises: f62339b118bb
Create Date: 2025-11-20 20:05:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "2a4d3b9c2e10"
down_revision: Union[str, Sequence[str], None] = "f62339b118bb"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add shipping_address_id and billing_address_id columns to orders."""
    op.add_column("orders", sa.Column("shipping_address_id", sa.Uuid(), nullable=True))
    op.add_column("orders", sa.Column("billing_address_id", sa.Uuid(), nullable=True))
    # Add foreign keys (SET NULL on delete)
    try:
        op.create_foreign_key(
            "fk_orders_shipping_address_id_addresses",
            "orders",
            "addresses",
            ["shipping_address_id"],
            ["id"],
            ondelete="SET NULL",
        )
    except Exception:  # pragma: no cover - best effort
        pass
    try:
        op.create_foreign_key(
            "fk_orders_billing_address_id_addresses",
            "orders",
            "addresses",
            ["billing_address_id"],
            ["id"],
            ondelete="SET NULL",
        )
    except Exception:  # pragma: no cover
        pass
    op.create_index("ix_orders_shipping_address_id", "orders", ["shipping_address_id"], unique=False)
    op.create_index("ix_orders_billing_address_id", "orders", ["billing_address_id"], unique=False)


def downgrade() -> None:
    """Remove shipping_address_id and billing_address_id columns from orders."""
    # Drop indexes first
    op.drop_index("ix_orders_billing_address_id", table_name="orders")
    op.drop_index("ix_orders_shipping_address_id", table_name="orders")
    # Drop foreign keys (names must match if created)
    try:
        op.drop_constraint("fk_orders_billing_address_id_addresses", "orders", type_="foreignkey")
    except Exception:  # pragma: no cover
        pass
    try:
        op.drop_constraint("fk_orders_shipping_address_id_addresses", "orders", type_="foreignkey")
    except Exception:  # pragma: no cover
        pass
    op.drop_column("orders", "billing_address_id")
    op.drop_column("orders", "shipping_address_id")
