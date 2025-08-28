"""Authentication utilities for Telegram bot with custom email templates."""

import json
import re
import secrets
from datetime import datetime, timedelta, timezone
from typing import List, Optional

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

    def _get_email_content(self, code: str, lang: str) -> tuple[str, str, Optional[str]]:
        """
        Get email subject, body, and HTML body for authentication code.
        Uses custom templates if configured, otherwise falls back to default i18n.

        Returns:
            tuple of (subject, plain_body, html_body)
        """
        bot_name = self.bot.name

        # Check if bot has custom templates
        has_custom_template = (
                self.bot.auth_email_subject_template or
                self.bot.auth_email_body_template or
                self.bot.auth_email_html_template
        )

        if has_custom_template:
            # Use custom templates
            # Subject
            if self.bot.auth_email_subject_template:
                subject = self.bot.auth_email_subject_template.format(
                    bot_name=bot_name,
                    code=code
                )
            else:
                subject = t("auth.email_subject", lang=lang, bot_name=bot_name)

            # Plain text body
            if self.bot.auth_email_body_template:
                body = self.bot.auth_email_body_template.format(
                    bot_name=bot_name,
                    code=code
                )
            else:
                body = t("auth.email_body", lang=lang, code=code)

            # HTML body (optional)
            html_body = None
            if self.bot.auth_email_html_template:
                html_body = self.bot.auth_email_html_template.format(
                    bot_name=bot_name,
                    code=code
                )

            return subject, body, html_body

        else:
            # Use default i18n templates
            subject = t("auth.email_subject", lang=lang, bot_name=bot_name)
            body = t("auth.email_body", lang=lang, code=code)

            # Default HTML template
            html_body = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <style>
                    body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                    .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                    .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }}
                    .content {{ background: #f8f9fa; padding: 30px; border-radius: 0 0 10px 10px; }}
                    .code-box {{ background: white; border: 2px solid #667eea; border-radius: 8px; padding: 20px; margin: 20px 0; text-align: center; }}
                    .code {{ font-size: 32px; font-weight: bold; color: #667eea; letter-spacing: 3px; }}
                    .footer {{ text-align: center; margin-top: 30px; color: #666; font-size: 12px; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>{bot_name}</h1>
                        <p style="margin: 0; opacity: 0.9;">Verification Code</p>
                    </div>
                    <div class="content">
                        <p>Your verification code is:</p>
                        <div class="code-box">
                            <div class="code">{code}</div>
                        </div>
                        <p>This code expires in 5 minutes.</p>
                        <div class="footer">
                            <p>If you didn't request this code, please ignore this email.</p>
                        </div>
                    </div>
                </div>
            </body>
            </html>
            """

            return subject, body, html_body

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
        """Handle email authentication request with custom templates."""
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

        # Get email content (with custom templates if configured)
        subject, body, html_body = self._get_email_content(code, lang)

        # Send email with code
        try:
            from ....utils.mailer import send_email
            send_email(
                to_email=email,
                subject=subject,
                body=body,
                html_body=html_body  # Can be None if not using HTML template
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
