import asyncio
from typing import Dict
from datetime import datetime
from sqlalchemy.orm import Session
from ..models.bot import Bot
from ..services.telegram_service import TelegramService
from ..services.discord.service import DiscordService
from ..utils.logger import get_logger

logger = get_logger(__name__)


class BotManager:
    """Singleton manager for all bot instances."""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.telegram_bots: Dict[str, TelegramService] = {}
            cls._instance.discord_bots: Dict[str, DiscordService] = {}  # New
            cls._instance.tasks: Dict[str, asyncio.Task] = {}
        return cls._instance

    async def start_bot(self, bot: Bot, db: Session) -> bool:
        """Start a bot (Telegram or Discord)."""
        try:
            # Start Telegram bot if configured
            if bot.telegram_bot_token:
                await self._start_telegram_bot(bot, db)

            # Start Discord bot if configured
            if bot.discord_bot_token:
                await self._start_discord_bot(bot, db)

            return True
        except Exception as e:
            logger.error(f"Failed to start bot {bot.name}: {str(e)}")
            return False

    async def _start_telegram_bot(self, bot: Bot, db: Session) -> bool:
        """Start a Telegram bot."""
        try:
            if bot.id in self.telegram_bots:
                await self.stop_telegram_bot(bot.id)

            telegram_service = TelegramService(bot, db)
            if await telegram_service.initialize():
                self.telegram_bots[bot.id] = telegram_service

                # Start polling in background
                task = asyncio.create_task(telegram_service.start_polling())
                self.tasks[f"telegram_{bot.id}"] = task

                # Update bot status
                bot.is_telegram_connected = True
                bot.last_health_check = datetime.utcnow()
                bot.health_status = "healthy"
                db.commit()

                logger.info(f"Started Telegram bot: {bot.name}")
                return True
            else:
                bot.is_telegram_connected = False
                bot.health_status = "unhealthy"
                db.commit()
                return False

        except Exception as e:
            logger.error(f"Failed to start Telegram bot {bot.name}: {str(e)}")
            bot.is_telegram_connected = False
            bot.health_status = "unhealthy"
            db.commit()
            return False

    async def _start_discord_bot(self, bot: Bot, db: Session) -> bool:
        """Start a Discord bot."""
        try:
            if bot.id in self.discord_bots:
                await self.stop_discord_bot(bot.id)

            discord_service = DiscordService(bot, db)
            if await discord_service.initialize():
                self.discord_bots[bot.id] = discord_service

                # Start Discord bot in background
                task = asyncio.create_task(discord_service.start())
                self.tasks[f"discord_{bot.id}"] = task

                # Update bot status
                bot.is_discord_connected = True
                bot.last_health_check = datetime.utcnow()
                bot.health_status = "healthy"
                db.commit()

                logger.info(f"Started Discord bot: {bot.name}")
                return True
            else:
                bot.is_discord_connected = False
                bot.health_status = "unhealthy"
                db.commit()
                return False

        except Exception as e:
            logger.error(f"Failed to start Discord bot {bot.name}: {str(e)}")
            bot.is_discord_connected = False
            bot.health_status = "unhealthy"
            db.commit()
            return False

    async def stop_bot(self, bot_id: str) -> bool:
        """Stop all bot instances (Telegram and Discord)."""
        try:
            stopped_telegram = await self.stop_telegram_bot(bot_id)
            stopped_discord = await self.stop_discord_bot(bot_id)
            return stopped_telegram or stopped_discord
        except Exception as e:
            logger.error(f"Failed to stop bot {bot_id}: {str(e)}")
            return False

    async def stop_telegram_bot(self, bot_id: str) -> bool:
        """Stop a Telegram bot."""
        try:
            if bot_id in self.telegram_bots:
                await self.telegram_bots[bot_id].stop()
                del self.telegram_bots[bot_id]

            task_key = f"telegram_{bot_id}"
            if task_key in self.tasks:
                self.tasks[task_key].cancel()
                try:
                    await self.tasks[task_key]
                except asyncio.CancelledError:
                    pass
                del self.tasks[task_key]

            logger.info(f"Stopped Telegram bot: {bot_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to stop Telegram bot {bot_id}: {str(e)}")
            return False

    async def stop_discord_bot(self, bot_id: str) -> bool:
        """Stop a Discord bot."""
        try:
            if bot_id in self.discord_bots:
                await self.discord_bots[bot_id].stop()
                del self.discord_bots[bot_id]

            task_key = f"discord_{bot_id}"
            if task_key in self.tasks:
                self.tasks[task_key].cancel()
                try:
                    await self.tasks[task_key]
                except asyncio.CancelledError:
                    pass
                del self.tasks[task_key]

            logger.info(f"Stopped Discord bot: {bot_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to stop Discord bot {bot_id}: {str(e)}")
            return False

    async def restart_bot(self, bot: Bot, db: Session) -> bool:
        """Restart all bot instances."""
        await self.stop_bot(bot.id)
        return await self.start_bot(bot, db)

    def get_bot_status(self, bot_id: str) -> Dict[str, any]:
        """Get bot status."""
        return {
            "is_telegram_running": bot_id in self.telegram_bots,
            "is_discord_running": bot_id in self.discord_bots,
            "is_running": bot_id in self.telegram_bots or bot_id in self.discord_bots,
            "has_telegram_task": f"telegram_{bot_id}" in self.tasks,
            "has_discord_task": f"discord_{bot_id}" in self.tasks
        }

    async def stop_all(self):
        """Stop all bots."""
        for bot_id in list(self.telegram_bots.keys()):
            await self.stop_telegram_bot(bot_id)
        for bot_id in list(self.discord_bots.keys()):
            await self.stop_discord_bot(bot_id)


bot_manager = BotManager()
