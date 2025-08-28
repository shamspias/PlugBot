"""add email template fields to bots

Revision ID: 008
Revises: 007
Create Date: 2025-01-09 00:00:00
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers
revision = '008'
down_revision = '007'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add email template fields to bots table
    op.add_column(
        'bots',
        sa.Column(
            'auth_email_subject_template',
            sa.Text(),
            nullable=True,
            comment='Custom email subject template for auth codes. Use {bot_name} as placeholder'
        ),
    )
    op.add_column(
        'bots',
        sa.Column(
            'auth_email_body_template',
            sa.Text(),
            nullable=True,
            comment='Custom email body template for auth codes. Use {code} and {bot_name} as placeholders'
        ),
    )
    op.add_column(
        'bots',
        sa.Column(
            'auth_email_html_template',
            sa.Text(),
            nullable=True,
            comment='Custom HTML email template for auth codes. Use {code} and {bot_name} as placeholders'
        ),
    )


def downgrade() -> None:
    op.drop_column('bots', 'auth_email_html_template')
    op.drop_column('bots', 'auth_email_body_template')
    op.drop_column('bots', 'auth_email_subject_template')
