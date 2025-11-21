"""add is_active column to categories

Revision ID: add_is_active_categories
Revises: 3b7f1a2c4d5e_address_table_refactor
Create Date: 2024-11-21 00:00:00
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'add_is_active_categories'
down_revision: Union[str, None] = '3b7f1a2c4d5e_address_table_refactor'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add column with server default True, then drop default to persist True values but not enforce future migrations.
    op.add_column('categories', sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.true()))
    # Optionally remove server default (keep application-level default)
    op.alter_column('categories', 'is_active', server_default=None)


def downgrade() -> None:
    op.drop_column('categories', 'is_active')
