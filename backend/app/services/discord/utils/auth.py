"""Authentication utilities for Discord bot."""

import json
import re
import secrets
from datetime import datetime, timedelta, timezone
from typing import List

import redis
import discord
from ....core.config import settings
from ....models.auth import AuthCode
from ....utils.logger import get_logger

logger = get_logger(__name__)


class AuthManager:
    """Manages authentication for Discord bot users."""

    def __init__(self, bot, db):
        self.bot = bot
        self.db = db
        self.redis = redis.Redis.from_url(settings.REDIS_URL, decode_responses=True)

    def _auth_key(self, discord_user_id: str) -> str:
        """Generate Redis key for authenticated user."""
        return f"discord_auth:{self.bot.id}:{discord_user_id}"

    def _pending_key(self, discord_user_id: str) -> str:
        """Generate Redis key for pending authentication."""
        return f"discord_pending:{self.bot.id}:{discord_user_id}"

    def is_authenticated(self, discord_user_id: str) -> bool:
        """Check if user is authenticated."""
        return self.redis.exists(self._auth_key(discord_user_id)) == 1

    def set_authenticated(self, discord_user_id: str, email: str):
        """Mark user as authenticated."""
        self.redis.set(self._auth_key(discord_user_id), json.dumps({"email": email}))

    def clear_authenticated(self, discord_user_id: str):
        """Clear user authentication."""
        self.redis.delete(self._auth_key(discord_user_id))
        self.redis.delete(self._pending_key(discord_user_id))

    def get_allowed_domains(self) -> List[str]:
        """Get list of allowed email domains."""
        if not self.bot.allowed_email_domains:
            return []
        return [
            d.strip().lstrip("@").lower()
            for d in self.bot.allowed_email_domains.split(",")
            if d.strip()
        ]

    async def auth_gate(self, message: discord.Message, bot) -> bool:
        """
        Check if user is authorized to use the bot.
        Returns True if the user is allowed to proceed.
        """
        if not bot.auth_required:
            return True

        user_id = str(message.author.id)
        content = message.content.strip()

        # Already authenticated?
        if self.is_authenticated(user_id):
            return True

        # Check if it's a 6-digit code
        if re.fullmatch(r"\d{6}", content):
            return await self._handle_auth_code(user_id, content, message)

        # Check if it looks like an email
        if self._looks_like_email(content):
            return await self._handle_email_auth(user_id, content, message, bot)

        # Not authenticated, prompt for email
        await self._prompt_for_auth(message)
        return False

    def _looks_like_email(self, text: str) -> bool:
        """Check if text looks like an email address."""
        return bool(
            re.fullmatch(
                r"[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}", text.strip()
            )
        )

    async def _handle_auth_code(self, user_id: str, code: str, message: discord.Message) -> bool:
        """Handle 6-digit authentication code."""
        now = datetime.now(timezone.utc)
        pending_email = self.redis.get(self._pending_key(user_id))

        q = (
            self.db.query(AuthCode)
            .filter(
                AuthCode.bot_id == self.bot.id,
                AuthCode.is_used == False,
                AuthCode.expires_at > now,
                AuthCode.code == code,
            )
            .order_by(AuthCode.created_at.desc())
        )

        if pending_email:
            q = q.filter(AuthCode.email == pending_email)

        code_row = q.first()

        if code_row:
            code_row.is_used = True
            code_row.used_at = now
            self.db.commit()
            self.set_authenticated(user_id, code_row.email)
            self.redis.delete(self._pending_key(user_id))

            embed = discord.Embed(
                description="✅ Authentication successful! You can now chat.",
                color=discord.Color.green()
            )
            await message.channel.send(embed=embed)
            return False
        else:
            embed = discord.Embed(
                description="❌ Invalid or expired code. Please send your email again.",
                color=discord.Color.red()
            )
            await message.channel.send(embed=embed)
            return False

    async def _handle_email_auth(self, user_id: str, email: str, message: discord.Message, bot) -> bool:
        """Handle email authentication request."""
        if not self._email_ok_for_bot(email, bot):
            domains = self.get_allowed_domains()
            domains_str = ", ".join(domains) or "(none configured)"

            embed = discord.Embed(
                description=f"🚫 Email not allowed. Allowed domains: {domains_str}",
                color=discord.Color.red()
            )
            await message.channel.send(embed=embed)
            return False

        # Generate and store 6-digit code
        code = f"{secrets.randbelow(1_000_000):06d}"
        expires_at = datetime.now(timezone.utc) + timedelta(minutes=5)

        ac = AuthCode(
            bot_id=bot.id,
            email=email,
            code=code,
            expires_at=expires_at
        )
        self.db.add(ac)
        self.db.commit()

        self.redis.setex(self._pending_key(user_id), 300, email)

        # Send email with code
        try:
            from ....utils.mailer import send_email
            send_email(
                to_email=email,
                subject=f"Your {bot.name} verification code",
                body=f"Your verification code is: {code}\nIt expires in 5 minutes.",
            )
        except Exception as e:
            logger.error(f"Failed to send code to {email}: {e}")
            embed = discord.Embed(
                description="❌ Could not send email. Please try again later.",
                color=discord.Color.red()
            )
            await message.channel.send(embed=embed)
            return False

        embed = discord.Embed(
            description="📧 I've emailed you a 6-digit code. Reply here with the code to continue (expires in 5 minutes).",
            color=discord.Color.blue()
        )
        await message.channel.send(embed=embed)
        return False

    def _email_ok_for_bot(self, email: str, bot) -> bool:
        """Check if email is allowed for this bot."""
        allowed = self.get_allowed_domains()
        if not allowed:
            return True
        if "@" not in email:
            return False
        domain = email.split("@", 1)[1].lower()
        return domain in allowed

    async def _prompt_for_auth(self, message: discord.Message):
        """Prompt user for authentication."""
        domains = self.get_allowed_domains()
        domains_hint = ""
        if domains:
            domains_hint = f" (allowed domains: {', '.join(domains)})"

        embed = discord.Embed(
            description=f"🔐 Please send your email to authenticate{domains_hint}.",
            color=discord.Color.blue()
        )
        await message.channel.send(embed=embed)
