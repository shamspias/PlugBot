"""
Very light-weight Telegram webhook endpoint, **only used when you configure a public
`TELEGRAM_WEBHOOK_URL` in settings**.
If you are just polling (the default in the service layer) you can ignore this file.
"""
from fastapi import APIRouter, Request, HTTPException, status, Depends
from sqlalchemy.orm import Session
from ...core.database import db_manager
from ...models.bot import Bot
from ...services.bot_manager import bot_manager
from ...utils.logger import get_logger

router = APIRouter(prefix="/webhooks", tags=["webhooks"])
logger = get_logger(__name__)


@router.post("/telegram/{bot_id}")
async def telegram_webhook(
        bot_id: str,
        request: Request,
        db: Session = Depends(db_manager.get_db)
):
    bot = db.query(Bot).filter(Bot.id == bot_id).first()
    if not bot or not bot_manager.get_bot_status(bot_id)["is_running"]:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Bot not running")

    body = await request.json()
    # Forward raw update to python-telegram-bot
    await bot_manager.bots[bot_id].application.update_queue.put(body)
    return {"status": "accepted"}
