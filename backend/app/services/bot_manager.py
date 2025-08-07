import asyncio
from typing import Dict, Optional
from sqlalchemy.orm import Session
from ..models.bot import Bot
from ..services.telegram_service import TelegramService
from ..utils.logger import get_logger

logger = get_logger(__name__)


class BotManager:
    """Singleton manager for all bot instances."""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.bots: Dict[str, TelegramService] = {}
            cls._instance.tasks: Dict[str, asyncio.Task] = {}
        return cls._instance

    async def start_bot(self, bot: Bot, db: Session) -> bool:
        """Start a Telegram bot."""
        try:
            if bot.id in self.bots:
                await self.stop_bot(bot.id)

            telegram_service = TelegramService(bot, db)
            if await telegram_service.initialize():
                self.bots[bot.id] = telegram_service

                # Start polling in background
                task = asyncio.create_task(telegram_service.start_polling())
                self.tasks[bot.id] = task

                # Update bot status
                bot.is_telegram_connected = True
                bot.last_health_check = datetime.utcnow()
                bot.health_status = "healthy"
                db.commit()

                logger.info(f"Started bot: {bot.name}")
                return True
            else:
                bot.is_telegram_connected = False
                bot.health_status = "unhealthy"
                db.commit()
                return False

        except Exception as e:
            logger.error(f"Failed to start bot {bot.name}: {str(e)}")
            bot.is_telegram_connected = False
            bot.health_status = "unhealthy"
            db.commit()
            return False

    async def stop_bot(self, bot_id: str) -> bool:
        """Stop a Telegram bot."""
        try:
            if bot_id in self.bots:
                await self.bots[bot_id].stop()
                del self.bots[bot_id]

            if bot_id in self.tasks:
                self.tasks[bot_id].cancel()
                del self.tasks[bot_id]

            logger.info(f"Stopped bot: {bot_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to stop bot {bot_id}: {str(e)}")
            return False

    async def restart_bot(self, bot: Bot, db: Session) -> bool:
        """Restart a Telegram bot."""
        await self.stop_bot(bot.id)
        return await self.start_bot(bot, db)

    def get_bot_status(self, bot_id: str) -> Dict[str, any]:
        """Get bot status."""
        return {
            "is_running": bot_id in self.bots,
            "has_task": bot_id in self.tasks
        }

    async def stop_all(self):
        """Stop all bots."""
        for bot_id in list(self.bots.keys()):
            await self.stop_bot(bot_id)


bot_manager = BotManager()

# backend/app/schemas/bot.py
from pydantic import BaseModel, Field, validator
from typing import Optional
from datetime import datetime


class BotBase(BaseModel):
    """Base bot schema."""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    dify_endpoint: str = Field(..., min_length=1)
    dify_type: str = Field(default="chat", pattern="^(chat|agent|chatflow|workflow)$")
    response_mode: str = Field(default="streaming", pattern="^(streaming|blocking)$")
    max_tokens: int = Field(default=2000, ge=100, le=10000)
    temperature: int = Field(default=7, ge=0, le=10)
    auto_generate_title: bool = True
    enable_file_upload: bool = True


class BotCreate(BotBase):
    """Schema for creating a bot."""
    dify_api_key: str = Field(..., min_length=1)
    telegram_bot_token: Optional[str] = None

    @validator('dify_endpoint')
    def validate_endpoint(cls, v):
        if not v.startswith(('http://', 'https://')):
            raise ValueError('Endpoint must start with http:// or https://')
        return v.rstrip('/')


class BotUpdate(BaseModel):
    """Schema for updating a bot."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    dify_endpoint: Optional[str] = None
    dify_api_key: Optional[str] = None
    dify_type: Optional[str] = Field(None, pattern="^(chat|agent|chatflow|workflow)$")
    telegram_bot_token: Optional[str] = None
    response_mode: Optional[str] = Field(None, pattern="^(streaming|blocking)$")
    max_tokens: Optional[int] = Field(None, ge=100, le=10000)
    temperature: Optional[int] = Field(None, ge=0, le=10)
    auto_generate_title: Optional[bool] = None
    enable_file_upload: Optional[bool] = None
    is_active: Optional[bool] = None


class BotResponse(BotBase):
    """Bot response schema."""
    id: str
    is_active: bool
    is_telegram_connected: bool
    telegram_bot_username: Optional[str]
    last_health_check: Optional[datetime]
    health_status: str
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True


class BotStatus(BaseModel):
    """Bot status schema."""
    id: str
    name: str
    is_active: bool
    is_telegram_connected: bool
    health_status: str
    last_health_check: Optional[datetime]
    is_running: bool
    conversation_count: int = 0


# backend/app/schemas/conversation.py
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class ConversationResponse(BaseModel):
    """Conversation response schema."""
    id: str
    bot_id: str
    title: Optional[str]
    telegram_chat_id: str
    telegram_username: Optional[str]
    telegram_chat_type: Optional[str]
    is_active: bool
    message_count: int
    last_message_at: Optional[datetime]
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True


class MessageResponse(BaseModel):
    """Message response schema."""
    id: str
    conversation_id: str
    role: str
    content: str
    tokens_used: Optional[int]
    created_at: datetime

    class Config:
        from_attributes = True


# backend/app/api/v1/bots.py
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional
from ...core.database import db_manager
from ...models.bot import Bot
from ...models.conversation import Conversation
from ...schemas.bot import BotCreate, BotUpdate, BotResponse, BotStatus
from ...core.security import security_manager
from ...services.bot_manager import bot_manager
from ...services.dify_service import DifyService
from ...utils.logger import get_logger
from datetime import datetime

router = APIRouter(prefix="/bots", tags=["bots"])
logger = get_logger(__name__)


@router.post("/", response_model=BotResponse, status_code=status.HTTP_201_CREATED)
async def create_bot(
        bot_data: BotCreate,
        background_tasks: BackgroundTasks,
        db: Session = Depends(db_manager.get_db)
):
    """Create a new bot configuration."""
    # Check if bot name already exists
    existing = db.query(Bot).filter(Bot.name == bot_data.name).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Bot with this name already exists"
        )

    # Create bot
    bot = Bot(
        **bot_data.model_dump(exclude={"dify_api_key", "telegram_bot_token"})
    )

    # Encrypt sensitive data
    bot.dify_api_key = security_manager.encrypt_data(bot_data.dify_api_key)
    if bot_data.telegram_bot_token:
        bot.telegram_bot_token = security_manager.encrypt_data(bot_data.telegram_bot_token)

    db.add(bot)
    db.commit()
    db.refresh(bot)

    # Test Dify connection in background
    background_tasks.add_task(test_dify_connection, bot.id, db)

    # Start Telegram bot if token provided
    if bot_data.telegram_bot_token:
        background_tasks.add_task(start_telegram_bot, bot.id, db)

    return bot


@router.get("/", response_model=List[BotResponse])
async def get_bots(
        skip: int = 0,
        limit: int = 100,
        is_active: Optional[bool] = None,
        db: Session = Depends(db_manager.get_db)
):
    """Get all bots."""
    query = db.query(Bot)

    if is_active is not None:
        query = query.filter(Bot.is_active == is_active)

    bots = query.offset(skip).limit(limit).all()
    return bots


@router.get("/{bot_id}", response_model=BotResponse)
async def get_bot(bot_id: str, db: Session = Depends(db_manager.get_db)):
    """Get a specific bot."""
    bot = db.query(Bot).filter(Bot.id == bot_id).first()
    if not bot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bot not found"
        )
    return bot


@router.get("/{bot_id}/status", response_model=BotStatus)
async def get_bot_status(bot_id: str, db: Session = Depends(db_manager.get_db)):
    """Get bot status including running state."""
    bot = db.query(Bot).filter(Bot.id == bot_id).first()
    if not bot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bot not found"
        )

    # Get running status from bot manager
    manager_status = bot_manager.get_bot_status(bot_id)

    # Get conversation count
    conversation_count = db.query(Conversation).filter(
        Conversation.bot_id == bot_id
    ).count()

    return BotStatus(
        id=bot.id,
        name=bot.name,
        is_active=bot.is_active,
        is_telegram_connected=bot.is_telegram_connected,
        health_status=bot.health_status,
        last_health_check=bot.last_health_check,
        is_running=manager_status["is_running"],
        conversation_count=conversation_count
    )


@router.patch("/{bot_id}", response_model=BotResponse)
async def update_bot(
        bot_id: str,
        bot_update: BotUpdate,
        background_tasks: BackgroundTasks,
        db: Session = Depends(db_manager.get_db)
):
    """Update a bot configuration."""
    bot = db.query(Bot).filter(Bot.id == bot_id).first()
    if not bot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bot not found"
        )

    # Update fields
    update_data = bot_update.model_dump(exclude_unset=True)

    # Encrypt sensitive data if provided
    if "dify_api_key" in update_data:
        update_data["dify_api_key"] = security_manager.encrypt_data(update_data["dify_api_key"])
    if "telegram_bot_token" in update_data:
        update_data["telegram_bot_token"] = security_manager.encrypt_data(update_data["telegram_bot_token"])

    for field, value in update_data.items():
        setattr(bot, field, value)

    bot.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(bot)

    # Restart bot if it's running and critical fields changed
    if any(field in update_data for field in ["telegram_bot_token", "dify_endpoint", "dify_api_key"]):
        if bot_manager.get_bot_status(bot_id)["is_running"]:
            background_tasks.add_task(restart_telegram_bot, bot_id, db)

    return bot


@router.delete("/{bot_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_bot(
        bot_id: str,
        background_tasks: BackgroundTasks,
        db: Session = Depends(db_manager.get_db)
):
    """Delete a bot."""
    bot = db.query(Bot).filter(Bot.id == bot_id).first()
    if not bot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bot not found"
        )

    # Stop bot if running
    background_tasks.add_task(bot_manager.stop_bot, bot_id)

    # Delete bot (conversations will cascade delete)
    db.delete(bot)
    db.commit()

    return None


@router.post("/{bot_id}/start", response_model=dict)
async def start_bot(
        bot_id: str,
        background_tasks: BackgroundTasks,
        db: Session = Depends(db_manager.get_db)
):
    """Start a Telegram bot."""
    bot = db.query(Bot).filter(Bot.id == bot_id).first()
    if not bot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bot not found"
        )

    if not bot.telegram_bot_token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Telegram bot token not configured"
        )

    if bot_manager.get_bot_status(bot_id)["is_running"]:
        return {"message": "Bot is already running"}

    background_tasks.add_task(start_telegram_bot, bot_id, db)
    return {"message": "Bot start initiated"}


@router.post("/{bot_id}/stop", response_model=dict)
async def stop_bot(
        bot_id: str,
        background_tasks: BackgroundTasks,
        db: Session = Depends(db_manager.get_db)
):
    """Stop a Telegram bot."""
    bot = db.query(Bot).filter(Bot.id == bot_id).first()
    if not bot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bot not found"
        )

    if not bot_manager.get_bot_status(bot_id)["is_running"]:
        return {"message": "Bot is not running"}

    background_tasks.add_task(stop_telegram_bot, bot_id, db)
    return {"message": "Bot stop initiated"}


@router.post("/{bot_id}/restart", response_model=dict)
async def restart_bot(
        bot_id: str,
        background_tasks: BackgroundTasks,
        db: Session = Depends(db_manager.get_db)
):
    """Restart a Telegram bot."""
    bot = db.query(Bot).filter(Bot.id == bot_id).first()
    if not bot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bot not found"
        )

    if not bot.telegram_bot_token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Telegram bot token not configured"
        )

    background_tasks.add_task(restart_telegram_bot, bot_id, db)
    return {"message": "Bot restart initiated"}


@router.post("/{bot_id}/health-check", response_model=dict)
async def health_check(
        bot_id: str,
        db: Session = Depends(db_manager.get_db)
):
    """Check bot health status."""
    bot = db.query(Bot).filter(Bot.id == bot_id).first()
    if not bot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bot not found"
        )

    # Check Dify connection
    dify_service = DifyService(bot)
    dify_healthy = await dify_service.health_check()
    await dify_service.close()

    # Check Telegram status
    telegram_running = bot_manager.get_bot_status(bot_id)["is_running"]

    # Update bot health status
    bot.last_health_check = datetime.utcnow()
    if dify_healthy and (not bot.telegram_bot_token or telegram_running):
        bot.health_status = "healthy"
    else:
        bot.health_status = "unhealthy"

    db.commit()

    return {
        "dify_healthy": dify_healthy,
        "telegram_running": telegram_running,
        "overall_status": bot.health_status
    }


# Background tasks
async def test_dify_connection(bot_id: str, db: Session):
    """Test Dify API connection."""
    bot = db.query(Bot).filter(Bot.id == bot_id).first()
    if bot:
        dify_service = DifyService(bot)
        is_healthy = await dify_service.health_check()
        await dify_service.close()

        bot.last_health_check = datetime.utcnow()
        bot.health_status = "healthy" if is_healthy else "unhealthy"
        db.commit()


async def start_telegram_bot(bot_id: str, db: Session):
    """Start Telegram bot in background."""
    bot = db.query(Bot).filter(Bot.id == bot_id).first()
    if bot and bot.telegram_bot_token:
        await bot_manager.start_bot(bot, db)


async def stop_telegram_bot(bot_id: str, db: Session):
    """Stop Telegram bot in background."""
    await bot_manager.stop_bot(bot_id)
    bot = db.query(Bot).filter(Bot.id == bot_id).first()
    if bot:
        bot.is_telegram_connected = False
        db.commit()


async def restart_telegram_bot(bot_id: str, db: Session):
    """Restart Telegram bot in background."""
    bot = db.query(Bot).filter(Bot.id == bot_id).first()
    if bot:
        await bot_manager.restart_bot(bot, db)
