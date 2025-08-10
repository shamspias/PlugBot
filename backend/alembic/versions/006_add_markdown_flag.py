# backend/alembic/versions/006_add_markdown_flag.py
"""add telegram_markdown_enabled to bots

Revision ID: 006
Revises: 005
Create Date: 2025-08-09 12:00:00
"""
from alembic import op
import sqlalchemy as sa

revision = "006"
down_revision = "005"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "bots",
        sa.Column("telegram_markdown_enabled", sa.Boolean(), server_default=sa.text("false"), nullable=False),
    )


def downgrade():
    op.drop_column("bots", "telegram_markdown_enabled")
