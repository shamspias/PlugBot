"""add discord bot support

Revision ID: 008
Revises: 007
Create Date: 2025-08-17 00:00:00
"""
from alembic import op
import sqlalchemy as sa

revision = "008"
down_revision = "007"
branch_labels = None
depends_on = None


def upgrade():
    # Add Discord-related columns to bots table
    op.add_column(
        "bots",
        sa.Column("discord_bot_token", sa.String(500), nullable=True)
    )
    op.add_column(
        "bots",
        sa.Column("discord_bot_id", sa.String(255), nullable=True)
    )
    op.add_column(
        "bots",
        sa.Column("discord_bot_username", sa.String(255), nullable=True)
    )
    op.add_column(
        "bots",
        sa.Column("discord_webhook_secret", sa.String(255), nullable=True)
    )
    op.add_column(
        "bots",
        sa.Column("is_discord_connected", sa.Boolean(), server_default=sa.text("false"), nullable=False)
    )
    op.add_column(
        "bots",
        sa.Column("discord_markdown_enabled", sa.Boolean(), server_default=sa.text("false"), nullable=False)
    )

    # Add Discord-specific columns to conversations table
    op.add_column(
        "conversations",
        sa.Column("discord_channel_id", sa.String(255), nullable=True)
    )
    op.add_column(
        "conversations",
        sa.Column("discord_guild_id", sa.String(255), nullable=True)
    )
    op.add_column(
        "conversations",
        sa.Column("discord_user_id", sa.String(255), nullable=True)
    )
    op.add_column(
        "conversations",
        sa.Column("discord_username", sa.String(255), nullable=True)
    )
    op.add_column(
        "conversations",
        sa.Column("platform", sa.String(20), server_default='telegram', nullable=False)
    )

    # Add Discord message IDs to messages table
    op.add_column(
        "messages",
        sa.Column("discord_message_id", sa.String(255), nullable=True)
    )
    op.add_column(
        "messages",
        sa.Column("discord_channel_id", sa.String(255), nullable=True)
    )


def downgrade():
    op.drop_column("messages", "discord_channel_id")
    op.drop_column("messages", "discord_message_id")
    op.drop_column("conversations", "platform")
    op.drop_column("conversations", "discord_username")
    op.drop_column("conversations", "discord_user_id")
    op.drop_column("conversations", "discord_guild_id")
    op.drop_column("conversations", "discord_channel_id")
    op.drop_column("bots", "discord_markdown_enabled")
    op.drop_column("bots", "is_discord_connected")
    op.drop_column("bots", "discord_webhook_secret")
    op.drop_column("bots", "discord_bot_username")
    op.drop_column("bots", "discord_bot_id")
    op.drop_column("bots", "discord_bot_token")
