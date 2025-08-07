from sqlalchemy import Column, String, Boolean, DateTime, Text, JSON, Integer
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from ..core.database import Base
import uuid


class Bot(Base):
    """Bot model for storing Dify bot configurations."""

    __tablename__ = "bots"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), nullable=False, unique=True)
    description = Column(Text)

    # Dify Configuration
    dify_endpoint = Column(String(500), nullable=False)
    dify_api_key = Column(String(500), nullable=False)  # Encrypted
    dify_type = Column(String(50), default="chat")  # chat, agent, chatflow, workflow

    # Telegram Configuration
    telegram_bot_token = Column(String(500))  # Encrypted
    telegram_bot_username = Column(String(255))
    telegram_webhook_secret = Column(String(255))

    # Status
    is_active = Column(Boolean, default=True)
    is_telegram_connected = Column(Boolean, default=False)
    last_health_check = Column(DateTime(timezone=True))
    health_status = Column(String(50), default="unknown")  # healthy, unhealthy, unknown

    # Settings
    response_mode = Column(String(20), default="streaming")  # streaming or blocking
    max_tokens = Column(Integer, default=2000)
    temperature = Column(Integer, default=7)  # 0-10, will be divided by 10
    auto_generate_title = Column(Boolean, default=True)
    enable_file_upload = Column(Boolean, default=True)

    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    conversations = relationship("Conversation", back_populates="bot", cascade="all, delete-orphan")


# backend/app/models/conversation.py
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

    # Metadata
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

    # Metadata
    metadata = Column(JSON)
    tokens_used = Column(Integer)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    conversation = relationship("Conversation", back_populates="messages")
