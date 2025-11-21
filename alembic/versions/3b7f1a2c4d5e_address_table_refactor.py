"""refactor addresses table: add line1/line2/state; drop street & default flags

Revision ID: 3b7f1a2c4d5e
Revises: 2a4d3b9c2e10
Create Date: 2025-11-21 00:45:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "3b7f1a2c4d5e"
down_revision: Union[str, Sequence[str], None] = "2a4d3b9c2e10"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _has_column(table: str, column: str) -> bool:  # pragma: no cover - metadata inspection helper
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    cols = [c["name"] for c in inspector.get_columns(table)]
    return column in cols


def upgrade() -> None:
    """Perform in-place refactor of addresses table.

    Steps:
    1. Add new columns line1, line2, state (line1/state initially nullable or with default for data copy).
    2. Copy existing street values into line1 if street column exists.
    3. Drop legacy columns street, is_default_shipping, is_default_billing if they exist.
    4. Enforce NOT NULL on line1 and state.
    """
    # Add columns if not present (use batch for SQLite compatibility)
    with op.batch_alter_table("addresses") as batch:
        if not _has_column("addresses", "line1"):
            batch.add_column(sa.Column("line1", sa.String(), nullable=True))
        if not _has_column("addresses", "line2"):
            batch.add_column(sa.Column("line2", sa.String(), nullable=True))
        if not _has_column("addresses", "state"):
            batch.add_column(sa.Column("state", sa.String(), nullable=True))

    # Copy street -> line1 before dropping street
    bind = op.get_bind()
    if _has_column("addresses", "street") and _has_column("addresses", "line1"):
        bind.execute(sa.text("UPDATE addresses SET line1 = street WHERE line1 IS NULL"))

    # Drop legacy columns
    with op.batch_alter_table("addresses") as batch:
        for legacy in ("street", "is_default_shipping", "is_default_billing"):
            if _has_column("addresses", legacy):
                try:
                    batch.drop_column(legacy)
                except Exception:  # pragma: no cover - best effort on SQLite
                    pass

    # Set NOT NULL constraints
    with op.batch_alter_table("addresses") as batch:
        # Ensure line1 populated; if still null set placeholder
        bind.execute(sa.text("UPDATE addresses SET line1 = 'UNKNOWN' WHERE line1 IS NULL"))
        bind.execute(sa.text("UPDATE addresses SET state = 'UNKNOWN' WHERE state IS NULL"))
        batch.alter_column("line1", existing_type=sa.String(), nullable=False)
        batch.alter_column("state", existing_type=sa.String(), nullable=False)


def downgrade() -> None:
    """Recreate legacy columns and remove new ones (data loss for line2/state)."""
    # Re-add legacy columns
    with op.batch_alter_table("addresses") as batch:
        if not _has_column("addresses", "street"):
            batch.add_column(sa.Column("street", sa.String(), nullable=True))
        if not _has_column("addresses", "is_default_shipping"):
            batch.add_column(sa.Column("is_default_shipping", sa.Boolean(), nullable=True))
        if not _has_column("addresses", "is_default_billing"):
            batch.add_column(sa.Column("is_default_billing", sa.Boolean(), nullable=True))

    # Copy line1 back to street
    bind = op.get_bind()
    if _has_column("addresses", "street") and _has_column("addresses", "line1"):
        bind.execute(sa.text("UPDATE addresses SET street = line1 WHERE street IS NULL"))

    # Drop new columns
    with op.batch_alter_table("addresses") as batch:
        for new_col in ("line1", "line2", "state"):
            if _has_column("addresses", new_col):
                try:
                    batch.drop_column(new_col)
                except Exception:  # pragma: no cover
                    pass
