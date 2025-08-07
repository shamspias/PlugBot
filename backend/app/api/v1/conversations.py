from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from ...core.database import db_manager
from ...models.conversation import Conversation, Message
from ...schemas.conversation import ConversationResponse, MessageResponse
from ...utils.logger import get_logger

router = APIRouter(prefix="/conversations", tags=["conversations"])
logger = get_logger(__name__)


@router.get("/", response_model=List[ConversationResponse])
async def get_conversations(
        bot_id: Optional[str] = Query(None, description="Filter by bot ID"),
        telegram_chat_id: Optional[str] = Query(None, description="Filter by Telegram chat ID"),
        is_active: Optional[bool] = Query(None, description="Filter by active status"),
        skip: int = 0,
        limit: int = 100,
        db: Session = Depends(db_manager.get_db)
):
    """Get conversations with optional filters."""
    query = db.query(Conversation)

    if bot_id:
        query = query.filter(Conversation.bot_id == bot_id)
    if telegram_chat_id:
        query = query.filter(Conversation.telegram_chat_id == telegram_chat_id)
    if is_active is not None:
        query = query.filter(Conversation.is_active == is_active)

    conversations = query.order_by(Conversation.updated_at.desc()).offset(skip).limit(limit).all()
    return conversations


@router.get("/{conversation_id}", response_model=ConversationResponse)
async def get_conversation(conversation_id: str, db: Session = Depends(db_manager.get_db)):
    """Get a specific conversation."""
    conversation = db.query(Conversation).filter(Conversation.id == conversation_id).first()
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found"
        )
    return conversation


@router.get("/{conversation_id}/messages", response_model=List[MessageResponse])
async def get_conversation_messages(
        conversation_id: str,
        skip: int = 0,
        limit: int = 100,
        db: Session = Depends(db_manager.get_db)
):
    """Get messages for a conversation."""
    conversation = db.query(Conversation).filter(Conversation.id == conversation_id).first()
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found"
        )

    messages = db.query(Message).filter(
        Message.conversation_id == conversation_id
    ).order_by(Message.created_at.desc()).offset(skip).limit(limit).all()

    return messages


@router.delete("/{conversation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_conversation(conversation_id: str, db: Session = Depends(db_manager.get_db)):
    """Delete a conversation."""
    conversation = db.query(Conversation).filter(Conversation.id == conversation_id).first()
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found"
        )

    db.delete(conversation)
    db.commit()

    return None
