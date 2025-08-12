"""Authentication utilities for Telegram bot."""

import json
import re
import secrets
from datetime import datetime, timedelta, timezone
from typing import List

import redis
from telegram import Update
from telegram.ext import ContextTypes

from ....core.config import settings
from ....core.i18n import t
from ....models.auth import AuthCode
from ....utils.logger import get_logger

logger = get_logger(__name__)


class AuthManager:
    """Manages authentication for Telegram bot users."""

    def __init__(self, bot, db):
        self.bot = bot
        self.db = db
        self.redis = redis.Redis.from_url(settings.REDIS_URL, decode_responses=True)

    def _auth_key(self, telegram_user_id: str) -> str:
        """Generate Redis key for authenticated user."""
        return f"auth:{self.bot.id}:{telegram_user_id}"

    def _pending_key(self, telegram_user_id: str) -> str:
        """Generate Redis key for pending authentication."""
        return f"pending:{self.bot.id}:{telegram_user_id}"

    def is_authenticated(self, telegram_user_id: str) -> bool:
        """Check if user is authenticated."""
        return self.redis.exists(self._auth_key(telegram_user_id)) == 1

    def set_authenticated(self, telegram_user_id: str, email: str):
        """Mark user as authenticated."""
        self.redis.set(self._auth_key(telegram_user_id), json.dumps({"email": email}))

    def clear_authenticated(self, telegram_user_id: str):
        """Clear user authentication."""
        self.redis.delete(self._auth_key(telegram_user_id))
        self.redis.delete(self._pending_key(telegram_user_id))

    def get_allowed_domains(self) -> List[str]:
        """Get list of allowed email domains."""
        if not self.bot.allowed_email_domains:
            return []
        return [
            d.strip().lstrip("@").lower()
            for d in self.bot.allowed_email_domains.split(",")
            if d.strip()
        ]

    def email_ok_for_bot(self, email: str) -> bool:
        """Check if email is allowed for this bot."""
        allowed = self.get_allowed_domains()
        if not allowed:
            return True
        if "@" not in email:
            return False
        domain = email.split("@", 1)[1].lower()
        return domain in allowed

    def looks_like_email(self, text: str) -> bool:
        """Check if text looks like an email address."""
        return bool(
            re.fullmatch(
                r"[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}", text.strip()
            )
        )

    async def auth_gate(self, update: Update, context: ContextTypes.DEFAULT_TYPE, lang: str) -> bool:
        """
        Check if user is authorized to use the bot.
        Returns True if the user is allowed to proceed to Dify.
        """
        if not self.bot.auth_required:
            return True

        user_id = str(update.effective_user.id)
        text = (update.message.text or "").strip()

        # Already authenticated?
        if self.is_authenticated(user_id):
            return True

        # Check if it's a 6-digit code
        if re.fullmatch(r"\d{6}", text):
            return await self._handle_auth_code(user_id, text, update, lang)

        # Check if it looks like an email
        if self.looks_like_email(text):
            return await self._handle_email_auth(user_id, text, update, lang)

        # Not authenticated, prompt for email
        await self._prompt_for_auth(update, lang)
        return False

    async def _handle_auth_code(self, user_id: str, code: str, update: Update, lang: str) -> bool:
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
            await update.message.reply_text(t("auth.success", lang=lang))
            return False
        else:
            await update.message.reply_text(t("auth.invalid_code", lang=lang))
            return False

    async def _handle_email_auth(self, user_id: str, email: str, update: Update, lang: str) -> bool:
        """Handle email authentication request."""
        if not self.email_ok_for_bot(email):
            domains = ", ".join(self.get_allowed_domains()) or "(none configured)"
            await update.message.reply_text(
                t("auth.email_not_allowed", lang=lang, domains=domains)
            )
            return False

        # Generate and store 6-digit code
        code = f"{secrets.randbelow(1_000_000):06d}"
        expires_at = datetime.now(timezone.utc) + timedelta(minutes=5)

        ac = AuthCode(
            bot_id=self.bot.id,
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
                subject=t("auth.email_subject", lang=lang, bot_name=self.bot.name),
                body=t("auth.email_body", lang=lang, code=code),
            )
        except Exception as e:
            logger.error("Failed to send code to %s: %s", email, e)
            await update.message.reply_text(t("auth.email_failed", lang=lang))
            return False

        await update.message.reply_text(t("auth.code_sent", lang=lang))
        return False

    async def _prompt_for_auth(self, update: Update, lang: str):
        """Prompt user for authentication."""
        domains = self.get_allowed_domains()
        domains_hint = ""
        if domains:
            domains_hint = t("auth.domains_hint", lang=lang, domains=", ".join(domains))

        await update.message.reply_text(
            t("auth.required", lang=lang, domains_hint=domains_hint)
        )
