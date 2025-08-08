import asyncio
from typing import Dict, Optional
from datetime import datetime
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
                try:
                    await self.tasks[bot_id]
                except asyncio.CancelledError:
                    pass
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
