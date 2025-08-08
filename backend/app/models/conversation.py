from sqlalchemy import Column, String, Boolean, DateTime, Text, JSON, ForeignKey, Integer
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from ..core.database import Base
import uuid


class Conversation(Base):
    """Conversation model for tracking chat sessions."""

    __tablename__ = "conversations"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    bot_id = Column(String, ForeignKey("bots.id", ondelete="CASCADE"), nullable=False)

    # Dify conversation
    dify_conversation_id = Column(String(255))
    dify_user_id = Column(String(255))

    # Telegram conversation
    telegram_chat_id = Column(String(255), nullable=False)
    telegram_user_id = Column(String(255))
    telegram_username = Column(String(255))
    telegram_chat_type = Column(String(50))  # private, group, supergroup, channel

    # Conversation data
    title = Column(String(500))
    is_active = Column(Boolean, default=True)
    last_message_at = Column(DateTime(timezone=True))
    message_count = Column(Integer, default=0)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    bot = relationship("Bot", back_populates="conversations")
    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan")


class Message(Base):
    """Message model for storing conversation messages."""

    __tablename__ = "messages"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    conversation_id = Column(String, ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False)

    # Message data
    role = Column(String(20), nullable=False)  # user, assistant, system
    content = Column(Text, nullable=False)

    # Dify message data
    dify_message_id = Column(String(255))
    dify_task_id = Column(String(255))

    # Telegram message data
    telegram_message_id = Column(String(255))
    telegram_reply_to_message_id = Column(String(255))

    # Message metadata - renamed from 'metadata' to avoid SQLAlchemy reserved word
    message_metadata = Column(JSON)
    tokens_used = Column(Integer)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    conversation = relationship("Conversation", back_populates="messages")
