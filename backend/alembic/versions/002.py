"""Remove temperature and max_tokens columns

Revision ID: 002
Revises: 001
Create Date: 2025-01-08 00:00:00

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers
revision = '002'
down_revision = '001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Drop temperature and max_tokens columns from bots table
    op.drop_column('bots', 'temperature')
    op.drop_column('bots', 'max_tokens')


def downgrade() -> None:
    # Re-add columns if rolling back
    op.add_column('bots',
                  sa.Column('temperature', sa.Integer(), server_default='7', nullable=True)
                  )
    op.add_column('bots',
                  sa.Column('max_tokens', sa.Integer(), server_default='2000', nullable=True)
                  )
