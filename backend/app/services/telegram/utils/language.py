"""Language management utilities for Telegram bot."""

import redis
from ....core.config import settings
from ....utils.logger import get_logger

logger = get_logger(__name__)


class LanguageManager:
    """Manages user language preferences."""

    def __init__(self, bot):
        self.bot = bot
        self.redis = redis.Redis.from_url(settings.REDIS_URL, decode_responses=True)

    def get_user_language(self, user_id: str) -> str:
        """Get user's preferred language or default."""
        lang_key = f"lang:{self.bot.id}:{user_id}"
        user_lang = self.redis.get(lang_key)

        if user_lang:
            return user_lang

        # Return default language from settings
        return settings.DEFAULT_LANGUAGE

    def set_user_language(self, user_id: str, lang: str):
        """Set user's preferred language."""
        lang_key = f"lang:{self.bot.id}:{user_id}"
        self.redis.set(lang_key, lang)
        logger.info(f"Set language for user {user_id} to {lang}")
