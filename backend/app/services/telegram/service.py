"""Main Telegram service class - simplified and focused on core functionality."""

from __future__ import annotations

from typing import Optional
from sqlalchemy.orm import Session
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
)

from ...models.bot import Bot
from ...services.dify_service import DifyService
from ...utils.logger import get_logger
from .handlers.commands import CommandHandlers
from .handlers.messages import MessageHandlers
from .handlers.callbacks import CallbackHandlers
from .utils.auth import AuthManager
from .utils.language import LanguageManager
from .utils.helpers import BotHelpers

logger = get_logger(__name__)


class TelegramService:
    """Service for managing Telegram bot integration."""

    def __init__(self, bot: Bot, db: Session):
        self._bot = bot
        self.db = db
        self.token = BotHelpers.decrypt_token(bot.telegram_bot_token)
        self.application: Optional[Application] = None
        self.dify_service = DifyService(bot)
        self.running = False

        # Initialize managers
        self.auth_manager = AuthManager(bot, db)
        self.language_manager = LanguageManager(bot)

        # Initialize handlers
        self.command_handlers = CommandHandlers(self)
        self.message_handlers = MessageHandlers(self)
        self.callback_handlers = CallbackHandlers(self)

    @property
    def bot(self) -> Bot:
        return self._bot

    async def initialize(self) -> bool:
        """Initialize Telegram bot."""
        try:
            self.application = Application.builder().token(self.token).build()

            # Register command handlers
            self._register_command_handlers()

            # Register message handlers
            self._register_message_handlers()

            # Register callback handlers
            self.application.add_handler(
                CallbackQueryHandler(self.callback_handlers.handle_callback)
            )

            await self.application.initialize()
            await self._set_bot_commands()

            logger.info("Telegram bot %s initialized successfully", self.bot.name)
            return True

        except Exception as e:
            logger.error("Failed to initialize Telegram bot: %s", e)
            return False

    def _register_command_handlers(self):
        """Register all command handlers."""
        handlers = [
            ("start", self.command_handlers.handle_start),
            ("help", self.command_handlers.handle_help),
            ("new", self.command_handlers.handle_new_conversation),
            ("clear", self.command_handlers.handle_clear),
            ("history", self.command_handlers.handle_history),
            ("logout", self.command_handlers.handle_logout),
            ("language", self.command_handlers.handle_language),
            ("lang", self.command_handlers.handle_language),
        ]

        for command, handler in handlers:
            self.application.add_handler(CommandHandler(command, handler))

    def _register_message_handlers(self):
        """Register all message handlers."""
        self.application.add_handler(
            MessageHandler(
                filters.TEXT & ~filters.COMMAND,
                self.message_handlers.handle_message
            )
        )
        self.application.add_handler(
            MessageHandler(filters.Document.ALL, self.message_handlers.handle_document)
        )
        self.application.add_handler(
            MessageHandler(filters.PHOTO, self.message_handlers.handle_photo)
        )

    async def _set_bot_commands(self):
        """Set bot commands in Telegram."""
        await self.application.bot.set_my_commands([
            ("start", "Start the bot / Запустить бота"),
            ("help", "Show help message / Показать справку"),
            ("new", "Start a new conversation / Начать новый разговор"),
            ("clear", "Clear current conversation / Очистить текущий разговор"),
            ("history", "Show conversation history / История разговоров"),
            ("language", "Change language / Изменить язык"),
            ("logout", "Log out / Выйти"),
        ])

    async def start_polling(self):
        """Start polling for updates."""
        try:
            # Clear any existing webhook
            await BotHelpers.clear_webhook(self.application.bot)

            await self.application.start()
            await self.application.updater.start_polling(drop_pending_updates=True)
            self.running = True
            logger.info("Started polling for bot %s", self.bot.name)

        except Exception as e:
            logger.error("Failed to start polling: %s", e)

    async def stop(self):
        """Stop the bot."""
        if self.application and self.running:
            await self.application.updater.stop()
            await self.application.stop()
            await self.application.shutdown()
            self.running = False
            logger.info("Stopped bot %s", self.bot.name)
