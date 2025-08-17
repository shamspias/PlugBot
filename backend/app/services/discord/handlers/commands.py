"""Command handlers for Discord bot."""

from discord.ext import commands
import discord

from ....models.conversation import Conversation
from ....utils.logger import get_logger

logger = get_logger(__name__)


class CommandHandlers:
    """Handles all Discord command operations."""

    def __init__(self, discord_service):
        self.service = discord_service
        self.bot = discord_service.bot
        self.db = discord_service.db
        self.auth_manager = discord_service.auth_manager

    async def handle_help(self, ctx: commands.Context):
        """Handle !help command."""
        embed = discord.Embed(
            title=f"🤖 {self.bot.name} Help",
            description=self.bot.description or "AI Assistant powered by Dify",
            color=discord.Color.blue()
        )

        embed.add_field(
            name="Commands",
            value=(
                "**!help** - Show this help message\n"
                "**!new** - Start a new conversation\n"
                "**!clear** - Clear current conversation\n"
                "**!history** - Show recent conversations\n"
                "**!logout** - Log out and re-authenticate\n"
                "\nJust send me a message to start chatting!"
            ),
            inline=False
        )

        await ctx.send(embed=embed)

    async def handle_new_conversation(self, ctx: commands.Context):
        """Handle !new command to start new conversation."""
        channel_id = str(ctx.channel.id)
        user_id = str(ctx.author.id)

        # Deactivate existing conversation
        existing = (
            self.db.query(Conversation)
            .filter(
                Conversation.discord_channel_id == channel_id,
                Conversation.bot_id == self.bot.id,
                Conversation.is_active == True,
                Conversation.platform == 'discord'
            )
            .first()
        )

        if existing:
            existing.is_active = False
            self.db.commit()

        embed = discord.Embed(
            description="✨ Started a new conversation. Send me your message!",
            color=discord.Color.green()
        )
        await ctx.send(embed=embed)

    async def handle_clear(self, ctx: commands.Context):
        """Handle !clear command."""
        channel_id = str(ctx.channel.id)

        from ....models.conversation import Message

        conv = (
            self.db.query(Conversation)
            .filter(
                Conversation.discord_channel_id == channel_id,
                Conversation.bot_id == self.bot.id,
                Conversation.is_active == True,
                Conversation.platform == 'discord'
            )
            .first()
        )

        if not conv:
            embed = discord.Embed(
                description="Nothing to clear. You're already fresh ✨",
                color=discord.Color.orange()
            )
            await ctx.send(embed=embed)
            return

        self.db.query(Message).filter(Message.conversation_id == conv.id).delete()
        self.db.delete(conv)
        self.db.commit()

        embed = discord.Embed(
            description="🧹 Cleared. Your next message will start a new conversation.",
            color=discord.Color.green()
        )
        await ctx.send(embed=embed)

    async def handle_history(self, ctx: commands.Context):
        """Handle !history command."""
        channel_id = str(ctx.channel.id)

        conversations = (
            self.db.query(Conversation)
            .filter(
                Conversation.discord_channel_id == channel_id,
                Conversation.bot_id == self.bot.id,
                Conversation.platform == 'discord'
            )
            .order_by(Conversation.updated_at.desc())
            .limit(5)
            .all()
        )

        if not conversations:
            embed = discord.Embed(
                description="No conversation history found.",
                color=discord.Color.orange()
            )
            await ctx.send(embed=embed)
            return

        embed = discord.Embed(
            title="📚 Recent Conversations",
            color=discord.Color.blue()
        )

        for conv in conversations:
            status = "🟢" if conv.is_active else "⚪"
            title = conv.title or f"Untitled {conv.created_at.strftime('%Y-%m-%d %H:%M')}"
            embed.add_field(
                name=f"{status} {title}",
                value=f"Messages: {conv.message_count}",
                inline=False
            )

        await ctx.send(embed=embed)

    async def handle_logout(self, ctx: commands.Context):
        """Handle !logout command."""
        user_id = str(ctx.author.id)

        self.auth_manager.clear_authenticated(user_id)

        embed = discord.Embed(
            description="✅ You have been logged out. Send your email to authenticate again.",
            color=discord.Color.green()
        )
        await ctx.send(embed=embed)
