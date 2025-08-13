"""add app_settings table"""
from alembic import op
import sqlalchemy as sa

revision = "007"
down_revision = "006"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "app_settings",
        sa.Column("id", sa.String(), primary_key=True, nullable=False),
        sa.Column("project_name", sa.String(255), nullable=False),
        sa.Column("allow_registration", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
    )
    # optional: seed a single row named 'global'
    op.execute(
        "INSERT INTO app_settings (id, project_name, allow_registration) VALUES "
        "('global', 'PlugBot', false)"
    )


def downgrade():
    op.drop_table("app_settings")
