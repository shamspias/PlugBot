"""Event handlers for Discord bot."""

import discord
from ....utils.logger import get_logger

logger = get_logger(__name__)


class EventHandlers:
    """Handles Discord bot events."""

    def __init__(self, discord_service):
        self.service = discord_service
        self.bot = discord_service.bot
        self.db = discord_service.db
        self.message_handlers = discord_service.message_handlers

    async def on_ready(self):
        """Called when the Discord bot is ready."""
        logger.info(f"Discord bot {self.service.discord_bot.user} is ready!")

        # Update bot info in database
        self.bot.discord_bot_id = str(self.service.discord_bot.user.id)
        self.bot.discord_bot_username = str(self.service.discord_bot.user)
        self.bot.is_discord_connected = True
        self.db.commit()

        # Set bot status
        await self.service.discord_bot.change_presence(
            activity=discord.Activity(
                type=discord.ActivityType.listening,
                name="your messages | !help"
            )
        )

    async def on_message(self, message: discord.Message):
        """Handle incoming messages."""
        # Skip bot's own messages
        if message.author == self.service.discord_bot.user:
            return

        # Process commands
        await self.service.discord_bot.process_commands(message)

        # If not a command, handle as regular message
        if not message.content.startswith('!'):
            # Check for attachments
            if message.attachments:
                await self.message_handlers.handle_attachment(message)
            elif message.content:
                await self.message_handlers.handle_message(message)

    async def on_guild_join(self, guild: discord.Guild):
        """Called when bot joins a new guild."""
        logger.info(f"Bot joined guild: {guild.name} ({guild.id})")

        # Send welcome message to the system channel if available
        if guild.system_channel:
            embed = discord.Embed(
                title=f"Hello {guild.name}! 👋",
                description=(
                    f"I'm {self.bot.name}, your AI assistant powered by Dify.\n\n"
                    "Use `!help` to see available commands.\n"
                    "Just send me a message to start chatting!"
                ),
                color=discord.Color.green()
            )
            await guild.system_channel.send(embed=embed)

    async def on_guild_remove(self, guild: discord.Guild):
        """Called when bot is removed from a guild."""
        logger.info(f"Bot removed from guild: {guild.name} ({guild.id})")
