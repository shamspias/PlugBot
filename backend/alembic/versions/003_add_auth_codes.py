"""add auth_codes table
Revision ID: 003
Revises: 002
Create Date: 2025-08-08 00:00:00
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers
revision = "003"
down_revision = "002"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "auth_codes",
        sa.Column("id", sa.String(), primary_key=True, nullable=False),
        sa.Column("bot_id", sa.String(), sa.ForeignKey("bots.id", ondelete="CASCADE"), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("code", sa.String(length=64), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("used_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("is_used", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
    )
    op.create_index("ix_auth_codes_bot_id", "auth_codes", ["bot_id"])
    op.create_index("ix_auth_codes_email", "auth_codes", ["email"])
    op.create_index("ix_auth_codes_code", "auth_codes", ["code"])


def downgrade():
    op.drop_index("ix_auth_codes_code", table_name="auth_codes")
    op.drop_index("ix_auth_codes_email", table_name="auth_codes")
    op.drop_index("ix_auth_codes_bot_id", table_name="auth_codes")
    op.drop_table("auth_codes")
