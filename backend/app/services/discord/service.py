"""Main Discord service class - handles Discord bot integration."""

from __future__ import annotations

import discord
from discord.ext import commands
from sqlalchemy.orm import Session

from ...models.bot import Bot
from ...services.dify_service import DifyService
from ...utils.logger import get_logger
from .handlers.commands import CommandHandlers
from .handlers.messages import MessageHandlers
from .handlers.events import EventHandlers
from .utils.auth import AuthManager
from .utils.helpers import DiscordHelpers

logger = get_logger(__name__)


class DiscordService:
    """Service for managing Discord bot integration."""

    def __init__(self, bot_model: Bot, db: Session):
        self._bot_model = bot_model
        self.db = db
        self.token = DiscordHelpers.decrypt_token(bot_model.discord_bot_token)
        self.dify_service = DifyService(bot_model)
        self.running = False

        # Initialize Discord bot with intents
        intents = discord.Intents.default()
        intents.message_content = True
        intents.guilds = True
        intents.guild_messages = True
        intents.dm_messages = True

        self.discord_bot = commands.Bot(
            command_prefix='!',
            intents=intents,
            help_command=None  # We'll implement custom help
        )

        # Initialize managers
        self.auth_manager = AuthManager(bot_model, db)

        # Initialize handlers
        self.command_handlers = CommandHandlers(self)
        self.message_handlers = MessageHandlers(self)
        self.event_handlers = EventHandlers(self)

        self._setup_handlers()

    @property
    def bot(self) -> Bot:
        """Get the bot model."""
        return self._bot_model

    def _setup_handlers(self):
        """Setup all Discord event handlers and commands."""
        # Register event handlers
        self.discord_bot.event(self.event_handlers.on_ready)
        self.discord_bot.event(self.event_handlers.on_message)
        self.discord_bot.event(self.event_handlers.on_guild_join)
        self.discord_bot.event(self.event_handlers.on_guild_remove)

        # Register commands
        self._register_commands()

    def _register_commands(self):
        """Register all Discord commands."""

        @self.discord_bot.command(name='help')
        async def help_command(ctx):
            await self.command_handlers.handle_help(ctx)

        @self.discord_bot.command(name='new')
        async def new_command(ctx):
            await self.command_handlers.handle_new_conversation(ctx)

        @self.discord_bot.command(name='clear')
        async def clear_command(ctx):
            await self.command_handlers.handle_clear(ctx)

        @self.discord_bot.command(name='history')
        async def history_command(ctx):
            await self.command_handlers.handle_history(ctx)

        @self.discord_bot.command(name='logout')
        async def logout_command(ctx):
            await self.command_handlers.handle_logout(ctx)

    async def initialize(self) -> bool:
        """Initialize Discord bot."""
        try:
            logger.info(f"Discord bot {self.bot.name} initialized successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize Discord bot: {e}")
            return False

    async def start(self):
        """Start the Discord bot."""
        try:
            self.running = True
            await self.discord_bot.start(self.token)
        except Exception as e:
            logger.error(f"Failed to start Discord bot: {e}")
            self.running = False
            raise

    async def stop(self):
        """Stop the Discord bot."""
        if self.running:
            await self.discord_bot.close()
            self.running = False
            logger.info(f"Stopped Discord bot {self.bot.name}")
