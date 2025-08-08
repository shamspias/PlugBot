from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class ConversationResponse(BaseModel):
    """Conversation response schema."""
    id: str
    bot_id: str
    title: Optional[str] = None
    telegram_chat_id: str
    telegram_username: Optional[str] = None
    telegram_chat_type: Optional[str] = None
    is_active: bool
    message_count: int
    last_message_at: Optional[datetime] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class MessageResponse(BaseModel):
    """Message response schema."""
    id: str
    conversation_id: str
    role: str
    content: str
    tokens_used: Optional[int] = None
    created_at: datetime

    class Config:
        from_attributes = True
