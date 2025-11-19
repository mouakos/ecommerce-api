"""add addresses table

Revision ID: 3c2f1b7d8e90
Revises: 9ab6fc8e4143
Create Date: 2025-11-20
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel

# revision identifiers, used by Alembic.
revision: str = '3c2f1b7d8e90'
down_revision: Union[str, Sequence[str], None] = '9ab6fc8e4143'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema by creating addresses table."""
    op.create_table(
        'addresses',
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('user_id', sa.Uuid(), nullable=False),
        sa.Column('label', sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column('first_name', sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column('last_name', sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column('company', sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column('line1', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column('line2', sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column('city', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column('state', sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column('postal_code', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column('country', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column('phone_number', sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column('is_default_shipping', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('is_default_billing', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_addresses_user_id'), 'addresses', ['user_id'], unique=False)
    # Partial unique indexes for defaults (PostgreSQL). If other dialect, these will be ignored.
    dialect = op.get_bind().dialect.name
    if dialect == 'postgresql':
        op.execute(
            "CREATE UNIQUE INDEX IF NOT EXISTS addresses_user_default_shipping_idx ON addresses (user_id) WHERE is_default_shipping"
        )
        op.execute(
            "CREATE UNIQUE INDEX IF NOT EXISTS addresses_user_default_billing_idx ON addresses (user_id) WHERE is_default_billing"
        )


def downgrade() -> None:
    """Downgrade schema by dropping addresses table."""
    dialect = op.get_bind().dialect.name
    if dialect == 'postgresql':
        op.execute('DROP INDEX IF EXISTS addresses_user_default_shipping_idx')
        op.execute('DROP INDEX IF EXISTS addresses_user_default_billing_idx')
    op.drop_index(op.f('ix_addresses_user_id'), table_name='addresses')
    op.drop_table('addresses')
