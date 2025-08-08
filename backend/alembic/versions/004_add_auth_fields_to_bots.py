"""add auth_required and allowed_email_domains to bots

Revision ID: 004
Revises: 003
Create Date: 2025-08-08 20:05:00
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "004"
down_revision = "003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "bots",
        sa.Column("auth_required", sa.Boolean(), server_default=sa.text("false"), nullable=False),
    )
    op.add_column(
        "bots",
        sa.Column("allowed_email_domains", sa.Text(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("bots", "allowed_email_domains")
    op.drop_column("bots", "auth_required")
