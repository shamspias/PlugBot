"""Initial migration

Revision ID: 001
Revises:
Create Date: 2025-01-01 00:00:00

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create bots table
    op.create_table('bots',
                    sa.Column('id', sa.String(), nullable=False),
                    sa.Column('name', sa.String(length=255), nullable=False),
                    sa.Column('description', sa.Text(), nullable=True),
                    sa.Column('dify_endpoint', sa.String(length=500), nullable=False),
                    sa.Column('dify_api_key', sa.String(length=500), nullable=False),
                    sa.Column('dify_type', sa.String(length=50), server_default='chat', nullable=True),
                    sa.Column('telegram_bot_token', sa.String(length=500), nullable=True),
                    sa.Column('telegram_bot_username', sa.String(length=255), nullable=True),
                    sa.Column('telegram_webhook_secret', sa.String(length=255), nullable=True),
                    sa.Column('is_active', sa.Boolean(), server_default='true', nullable=True),
                    sa.Column('is_telegram_connected', sa.Boolean(), server_default='false', nullable=True),
                    sa.Column('last_health_check', sa.DateTime(timezone=True), nullable=True),
                    sa.Column('health_status', sa.String(length=50), server_default='unknown', nullable=True),
                    sa.Column('response_mode', sa.String(length=20), server_default='streaming', nullable=True),
                    sa.Column('max_tokens', sa.Integer(), server_default='2000', nullable=True),
                    sa.Column('temperature', sa.Integer(), server_default='7', nullable=True),
                    sa.Column('auto_generate_title', sa.Boolean(), server_default='true', nullable=True),
                    sa.Column('enable_file_upload', sa.Boolean(), server_default='true', nullable=True),
                    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
                    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
                    sa.PrimaryKeyConstraint('id'),
                    sa.UniqueConstraint('name')
                    )

    # Create conversations table
    op.create_table('conversations',
                    sa.Column('id', sa.String(), nullable=False),
                    sa.Column('bot_id', sa.String(), nullable=False),
                    sa.Column('dify_conversation_id', sa.String(length=255), nullable=True),
                    sa.Column('dify_user_id', sa.String(length=255), nullable=True),
                    sa.Column('telegram_chat_id', sa.String(length=255), nullable=False),
                    sa.Column('telegram_user_id', sa.String(length=255), nullable=True),
                    sa.Column('telegram_username', sa.String(length=255), nullable=True),
                    sa.Column('telegram_chat_type', sa.String(length=50), nullable=True),
                    sa.Column('title', sa.String(length=500), nullable=True),
                    sa.Column('is_active', sa.Boolean(), server_default='true', nullable=True),
                    sa.Column('last_message_at', sa.DateTime(timezone=True), nullable=True),
                    sa.Column('message_count', sa.Integer(), server_default='0', nullable=True),
                    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
                    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
                    sa.ForeignKeyConstraint(['bot_id'], ['bots.id'], ondelete='CASCADE'),
                    sa.PrimaryKeyConstraint('id')
                    )

    # Create messages table
    op.create_table('messages',
                    sa.Column('id', sa.String(), nullable=False),
                    sa.Column('conversation_id', sa.String(), nullable=False),
                    sa.Column('role', sa.String(length=20), nullable=False),
                    sa.Column('content', sa.Text(), nullable=False),
                    sa.Column('dify_message_id', sa.String(length=255), nullable=True),
                    sa.Column('dify_task_id', sa.String(length=255), nullable=True),
                    sa.Column('telegram_message_id', sa.String(length=255), nullable=True),
                    sa.Column('telegram_reply_to_message_id', sa.String(length=255), nullable=True),
                    sa.Column('message_metadata', sa.JSON(), nullable=True),  # Changed from 'metadata'
                    sa.Column('tokens_used', sa.Integer(), nullable=True),
                    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
                    sa.ForeignKeyConstraint(['conversation_id'], ['conversations.id'], ondelete='CASCADE'),
                    sa.PrimaryKeyConstraint('id')
                    )


def downgrade() -> None:
    op.drop_table('messages')
    op.drop_table('conversations')
    op.drop_table('bots')
