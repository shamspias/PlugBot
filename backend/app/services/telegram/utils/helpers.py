"""General helper utilities for Telegram bot."""

from ....core.security import security_manager
from ....utils.logger import get_logger

logger = get_logger(__name__)


class BotHelpers:
    """General helper functions for bot operations."""

    @staticmethod
    def decrypt_token(encrypted_token: str) -> str:
        """Decrypt bot token."""
        return security_manager.decrypt_data(encrypted_token)

    @staticmethod
    async def clear_webhook(bot):
        """Clear existing webhook if set."""
        try:
            info = await bot.get_webhook_info()
            if info and info.url:
                logger.info("Clearing existing webhook: %s", info.url)
                await bot.delete_webhook(drop_pending_updates=True)
        except Exception as e:
            logger.warning("Webhook check/delete failed: %s", e)
