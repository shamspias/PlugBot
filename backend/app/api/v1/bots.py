from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
import httpx

from ...core.database import db_manager
from ...core.security import security_manager
from ...models.bot import Bot
from ...models.conversation import Conversation
from ...schemas.bot import BotCreate, BotUpdate, BotResponse, BotStatus
from ...services.bot_manager import bot_manager
from ...services.dify_service import DifyService
from ...utils.logger import get_logger

from ...api.deps import get_current_user
from ...models.user import User

router = APIRouter(prefix="/bots", tags=["bots"])
logger = get_logger(__name__)


@router.get("/", response_model=List[BotResponse])
async def get_bots(
        skip: int = 0,
        limit: int = 100,
        is_active: Optional[bool] = Query(None, description="Filter by active status"),
        db: Session = Depends(db_manager.get_db),
        current_user: User = Depends(get_current_user)
):
    """Get all bots with optional filters."""
    query = db.query(Bot)

    if is_active is not None:
        query = query.filter(Bot.is_active == is_active)

    bots = query.offset(skip).limit(limit).all()
    return bots


@router.get("/{bot_id}", response_model=BotResponse)
async def get_bot(bot_id: str, db: Session = Depends(db_manager.get_db)):
    """Get a specific bot by ID."""
    bot = db.query(Bot).filter(Bot.id == bot_id).first()
    if not bot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bot not found"
        )
    return bot


@router.get("/{bot_id}/status", response_model=BotStatus)
async def get_bot_status(bot_id: str, db: Session = Depends(db_manager.get_db)):
    """Get bot status including running state and conversation count."""
    bot = db.query(Bot).filter(Bot.id == bot_id).first()
    if not bot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bot not found"
        )

    # Get bot running status
    bot_status = bot_manager.get_bot_status(bot_id)

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
        is_running=bot_status["is_running"],
        conversation_count=conversation_count
    )


@router.post("/", response_model=BotResponse, status_code=status.HTTP_201_CREATED)
async def create_bot(bot_data: BotCreate, db: Session = Depends(db_manager.get_db)):
    """Create a new bot."""
    # Check if bot name already exists
    existing_bot = db.query(Bot).filter(Bot.name == bot_data.name).first()
    if existing_bot:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Bot with this name already exists"
        )

    # Validate Dify endpoint and API key
    try:
        await validate_dify_connection(bot_data.dify_endpoint, bot_data.dify_api_key)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to connect to Dify: {str(e)}"
        )

    # Create bot
    bot = Bot(
        name=bot_data.name,
        description=bot_data.description,
        dify_endpoint=bot_data.dify_endpoint.rstrip('/'),
        dify_api_key=security_manager.encrypt_data(bot_data.dify_api_key),
        dify_type=bot_data.dify_type,
        response_mode=bot_data.response_mode,
        auto_generate_title=bot_data.auto_generate_title,
        enable_file_upload=bot_data.enable_file_upload,
        auth_required=bot_data.auth_required,
        allowed_email_domains=bot_data.allowed_email_domains
    )

    # Add Telegram token if provided
    if bot_data.telegram_bot_token:
        try:
            # Validate Telegram bot token
            telegram_info = await validate_telegram_token(bot_data.telegram_bot_token)
            bot.telegram_bot_token = security_manager.encrypt_data(bot_data.telegram_bot_token)
            bot.telegram_bot_username = telegram_info.get("username")
        except Exception as e:
            logger.warning(f"Telegram token validation failed: {str(e)}")
            # Still create bot but without Telegram integration

    db.add(bot)
    db.commit()
    db.refresh(bot)

    # Start bot if Telegram token is provided
    if bot.telegram_bot_token:
        try:
            await bot_manager.start_bot(bot, db)
            db.refresh(bot)
        except Exception as e:
            logger.error(f"Failed to start bot {bot.name}: {str(e)}")

    return bot


async def validate_telegram_token(token: str) -> dict:
    """Validate a Telegram bot token by calling getMe."""
    if not token or ":" not in token:
        raise ValueError("Malformed Telegram token")
    url = f"https://api.telegram.org/bot{token}/getMe"
    timeout = httpx.Timeout(10.0)
    async with httpx.AsyncClient(timeout=timeout) as client:
        r = await client.get(url)
        try:
            data = r.json()
        except Exception:
            raise ValueError(f"Telegram API returned non-JSON: {r.status_code}")
        if not data.get("ok"):
            desc = data.get("description", "Unknown error")
            raise ValueError(f"Telegram getMe failed: {desc}")
        # Return a tiny struct we use above
        user = data.get("result") or {}
        return {"username": user.get("username"), "id": user.get("id")}


@router.patch("/{bot_id}", response_model=BotResponse)
async def update_bot(
        bot_id: str,
        bot_update: BotUpdate,
        db: Session = Depends(db_manager.get_db)
):
    """Update an existing bot."""
    bot = db.query(Bot).filter(Bot.id == bot_id).first()
    if not bot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bot not found"
        )

    # Check if name is being updated and if it's unique
    if bot_update.name and bot_update.name != bot.name:
        existing = db.query(Bot).filter(Bot.name == bot_update.name).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Bot with this name already exists"
            )

    # Validate Dify connection if endpoint or API key is being updated
    if bot_update.dify_endpoint or bot_update.dify_api_key:
        endpoint = bot_update.dify_endpoint or bot.dify_endpoint
        api_key = bot_update.dify_api_key or security_manager.decrypt_data(bot.dify_api_key)
        try:
            await validate_dify_connection(endpoint, api_key)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to connect to Dify: {str(e)}"
            )

    # Update bot fields
    update_data = bot_update.dict(exclude_unset=True)

    # If dify_api_key was explicitly set to None (blank in form), ignore it to avoid wiping a valid key
    if "dify_api_key" in update_data and update_data["dify_api_key"] is None:
        update_data.pop("dify_api_key")

    # Encrypt sensitive data
    if "dify_api_key" in update_data:
        update_data["dify_api_key"] = security_manager.encrypt_data(update_data["dify_api_key"])

    # Handle Telegram token update
    if "telegram_bot_token" in update_data:
        if update_data["telegram_bot_token"]:
            try:
                telegram_info = await validate_telegram_token(update_data["telegram_bot_token"])
                update_data["telegram_bot_token"] = security_manager.encrypt_data(
                    update_data["telegram_bot_token"]
                )
                update_data["telegram_bot_username"] = telegram_info.get("username")
            except Exception as e:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid Telegram bot token: {str(e)}"
                )
        else:
            # Remove Telegram integration
            update_data["telegram_bot_token"] = None
            update_data["telegram_bot_username"] = None
            update_data["is_telegram_connected"] = False

    # Update bot
    for key, value in update_data.items():
        setattr(bot, key, value)

    bot.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(bot)

    # Restart bot if it's running
    if bot_manager.get_bot_status(bot_id)["is_running"]:
        await bot_manager.restart_bot(bot, db)

    return bot


@router.delete("/{bot_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_bot(bot_id: str, db: Session = Depends(db_manager.get_db)):
    """Delete a bot and all associated data."""
    bot = db.query(Bot).filter(Bot.id == bot_id).first()
    if not bot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bot not found"
        )

    # Stop bot if running
    if bot_manager.get_bot_status(bot_id)["is_running"]:
        await bot_manager.stop_bot(bot_id)

    # Delete bot (cascades to conversations and messages)
    db.delete(bot)
    db.commit()
    return None


@router.post("/{bot_id}/start")
async def start_bot(bot_id: str, db: Session = Depends(db_manager.get_db)):
    """Start a bot's Telegram service."""
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
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Bot is already running"
        )

    success = await bot_manager.start_bot(bot, db)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to start bot"
        )

    return {"message": "Bot started successfully"}


@router.post("/{bot_id}/stop")
async def stop_bot(bot_id: str, db: Session = Depends(db_manager.get_db)):
    """Stop a bot's Telegram service."""
    bot = db.query(Bot).filter(Bot.id == bot_id).first()
    if not bot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bot not found"
        )

    if not bot_manager.get_bot_status(bot_id)["is_running"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Bot is not running"
        )

    success = await bot_manager.stop_bot(bot_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to stop bot"
        )

    # Update bot status
    bot.is_telegram_connected = False
    db.commit()

    return {"message": "Bot stopped successfully"}


@router.post("/{bot_id}/restart")
async def restart_bot(bot_id: str, db: Session = Depends(db_manager.get_db)):
    """Restart a bot's Telegram service."""
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

    success = await bot_manager.restart_bot(bot, db)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to restart bot"
        )

    return {"message": "Bot restarted successfully"}


@router.post("/{bot_id}/health-check")
async def health_check(bot_id: str, db: Session = Depends(db_manager.get_db)):
    """Perform health check on bot's Dify connection."""
    bot = db.query(Bot).filter(Bot.id == bot_id).first()
    if not bot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bot not found"
        )

    # Check Dify connection
    dify_service = DifyService(bot)
    is_healthy = await dify_service.health_check()
    await dify_service.close()

    # Update bot health status
    bot.last_health_check = datetime.utcnow()
    bot.health_status = "healthy" if is_healthy else "unhealthy"
    db.commit()

    return {
        "dify_connection": is_healthy,
        "telegram_running": bot_manager.get_bot_status(bot_id)["is_running"],
        "health_status": bot.health_status,
        "checked_at": bot.last_health_check
    }


# Helper functions
async def validate_dify_connection(endpoint: str, api_key: str) -> bool:
    """Validate Dify endpoint and API key."""
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            # Try to access the Dify API parameters endpoint
            response = await client.get(
                f"{endpoint.rstrip('/')}/parameters",
                headers={"Authorization": f"Bearer {api_key}"}
            )

            if response.status_code == 401:
                raise ValueError("Invalid API key")
            elif response.status_code == 404:
                raise ValueError("Invalid endpoint - API not found")
            elif response.status_code != 200:
                raise ValueError(f"Unexpected response: {response.status_code}")

            return True
        except httpx.ConnectError:
            raise ValueError("Failed to connect to Dify endpoint")
        except httpx.TimeoutException:
            raise ValueError("Connection timeout - endpoint not responding")
        except Exception as e:
            raise ValueError(f"Connection failed: {str(e)}")
