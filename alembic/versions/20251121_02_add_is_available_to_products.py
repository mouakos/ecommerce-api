"""add is_available column to products

Revision ID: add_is_available_products
Revises: add_is_active_categories
Create Date: 2025-11-21 00:00:00
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'add_is_available_products'
down_revision: Union[str, None] = 'add_is_active_categories'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('products', sa.Column('is_available', sa.Boolean(), nullable=False, server_default=sa.true()))
    op.alter_column('products', 'is_available', server_default=None)


def downgrade() -> None:
    op.drop_column('products', 'is_available')
