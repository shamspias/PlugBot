from __future__ import annotations

import json
import re
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional, List

import redis
from sqlalchemy.orm import Session
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode, ChatAction
from telegram.error import BadRequest
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
)

from ..core.config import settings
from ..core.security import security_manager
from ..core.i18n import t  # Import translation function
from ..models.bot import Bot
from ..models.conversation import Conversation, Message
from ..models.auth import AuthCode
from ..services.dify_service import DifyService
from ..utils.logger import get_logger

try:
    from ..utils.mailer import send_email
except Exception:  # pragma: no cover
    def send_email(to_email: str, subject: str, body: str):
        raise RuntimeError(
            "Email sender not configured. Provide app/utils/mailer.py and SMTP env."
        )

logger = get_logger(__name__)


class TelegramService:
    """Service for managing Telegram bot integration."""

    def __init__(self, bot: Bot, db: Session):
        self._bot = bot
        self.db = db
        self.token = security_manager.decrypt_data(bot.telegram_bot_token)
        self.application: Optional[Application] = None
        self.dify_service = DifyService(bot)
        self.running = False
        # Redis for lightweight session of "who is authenticated"
        self.redis = redis.Redis.from_url(settings.REDIS_URL, decode_responses=True)
        # Store user language preferences
        self.user_languages = {}  # Will be stored in Redis in production

    @property
    def bot(self) -> Bot:
        return self._bot

    # ---------- LANGUAGE HELPERS ----------

    def _get_user_language(self, user_id: str) -> str:
        """Get user's preferred language or default."""
        # Check Redis for user preference
        lang_key = f"lang:{self.bot.id}:{user_id}"
        user_lang = self.redis.get(lang_key)
        if user_lang:
            return user_lang
        # Return default language from settings
        return settings.DEFAULT_LANGUAGE

    def _set_user_language(self, user_id: str, lang: str):
        """Set user's preferred language."""
        lang_key = f"lang:{self.bot.id}:{user_id}"
        self.redis.set(lang_key, lang)

    # ---------- AUTH HELPERS ----------

    def _auth_key(self, telegram_user_id: str) -> str:
        return f"auth:{self.bot.id}:{telegram_user_id}"

    def _pending_key(self, telegram_user_id: str) -> str:
        return f"pending:{self.bot.id}:{telegram_user_id}"

    def _is_authenticated(self, telegram_user_id: str) -> bool:
        return self.redis.exists(self._auth_key(telegram_user_id)) == 1

    def _set_authenticated(self, telegram_user_id: str, email: str):
        self.redis.set(self._auth_key(telegram_user_id), json.dumps({"email": email}))

    def _clear_authenticated(self, telegram_user_id: str):
        self.redis.delete(self._auth_key(telegram_user_id))
        self.redis.delete(self._pending_key(telegram_user_id))

    def _allowed_domains(self) -> List[str]:
        if not self.bot.allowed_email_domains:
            return []
        return [
            d.strip().lstrip("@").lower()
            for d in self.bot.allowed_email_domains.split(",")
            if d.strip()
        ]

    def _email_ok_for_bot(self, email: str) -> bool:
        allowed = self._allowed_domains()
        if not allowed:
            return True
        if "@" not in email:
            return False
        domain = email.split("@", 1)[1].lower()
        return domain in allowed

    def _looks_like_email(self, text: str) -> bool:
        return bool(
            re.fullmatch(
                r"[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}", text.strip()
            )
        )

    # ------- MARKDOWN -------

    def _escape_markdown_v2_minimal(self, text: str) -> str:
        """
        Minimal escape for Telegram MarkdownV2 that PRESERVES * and _ so **bold** and _italic_ work.
        """
        if not text:
            return text
        specials_to_escape = r"[]()~`>#+-=|{}.!\\"
        out = []
        for ch in text:
            if ch in specials_to_escape:
                out.append("\\" + ch)
            else:
                out.append(ch)
        return "".join(out)

    def _fmt(self, text: str, *, finalize: bool = False) -> dict:
        """
        Formatting helper for markdown support.
        """
        use_md = bool(getattr(self.bot, "telegram_markdown_enabled", False))
        safe_text = text if (text is not None and text != "") else "…"

        if not use_md:
            return {"text": safe_text}

        if finalize:
            return {
                "text": self._escape_markdown_v2_minimal(safe_text),
                "parse_mode": ParseMode.MARKDOWN_V2,
            }

        return {"text": safe_text}

    # ---------- LIFECYCLE ----------

    async def initialize(self) -> bool:
        """Initialize Telegram bot."""
        try:
            self.application = Application.builder().token(self.token).build()

            # Commands & handlers
            self.application.add_handler(CommandHandler("start", self.handle_start))
            self.application.add_handler(CommandHandler("help", self.handle_help))
            self.application.add_handler(CommandHandler("new", self.handle_new_conversation))
            self.application.add_handler(CommandHandler("clear", self.handle_clear))
            self.application.add_handler(CommandHandler("history", self.handle_history))
            self.application.add_handler(CommandHandler("logout", self.handle_logout))
            self.application.add_handler(CommandHandler("language", self.handle_language))
            self.application.add_handler(CommandHandler("lang", self.handle_language))

            # Messages
            self.application.add_handler(
                MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message)
            )
            self.application.add_handler(MessageHandler(filters.Document.ALL, self.handle_document))
            self.application.add_handler(MessageHandler(filters.PHOTO, self.handle_photo))

            # Callback buttons
            self.application.add_handler(CallbackQueryHandler(self.handle_callback))

            await self.application.initialize()
            await self.application.bot.set_my_commands(
                [
                    ("start", "Start the bot / Запустить бота"),
                    ("help", "Show help message / Показать справку"),
                    ("new", "Start a new conversation / Начать новый разговор"),
                    ("clear", "Clear current conversation / Очистить текущий разговор"),
                    ("history", "Show conversation history / История разговоров"),
                    ("language", "Change language / Изменить язык"),
                    ("logout", "Log out / Выйти"),
                ]
            )

            logger.info("Telegram bot %s initialized successfully", self.bot.name)
            return True
        except Exception as e:
            logger.error("Failed to initialize Telegram bot: %s", e)
            return False

    async def start_polling(self):
        """Start polling for updates."""
        try:
            try:
                info = await self.application.bot.get_webhook_info()
                if info and info.url:
                    logger.info("Clearing existing webhook: %s", info.url)
                    await self.application.bot.delete_webhook(drop_pending_updates=True)
            except Exception as e:
                logger.warning("Webhook check/delete failed: %s", e)

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

    # ---------- COMMANDS ----------

    async def handle_start(self, update: Update, context):
        """Handle /start command."""
        user_id = str(update.effective_user.id)
        lang = self._get_user_language(user_id)

        if self.bot.description:
            welcome_message = t("bot.welcome", lang=lang,
                                bot_name=self.bot.name,
                                description=self.bot.description)
        else:
            welcome_message = t("bot.welcome_no_desc", lang=lang,
                                bot_name=self.bot.name)

        await update.message.reply_text(welcome_message, parse_mode=ParseMode.MARKDOWN)

    async def handle_help(self, update: Update, context):
        """Handle /help command."""
        await self.handle_start(update, context)

    async def handle_language(self, update: Update, context):
        """Handle /language command to change user's language preference."""
        keyboard = [
            [
                InlineKeyboardButton("🇬🇧 English", callback_data="lang_en"),
                InlineKeyboardButton("🇷🇺 Русский", callback_data="lang_ru")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        user_id = str(update.effective_user.id)
        current_lang = self._get_user_language(user_id)

        # Send message in current language
        msg_text = "Choose your language / Выберите язык:"
        await update.message.reply_text(msg_text, reply_markup=reply_markup)

    async def handle_logout(self, update: Update, context):
        """Handle /logout command."""
        user_id = str(update.effective_user.id)
        lang = self._get_user_language(user_id)
        self._clear_authenticated(user_id)
        await update.message.reply_text(t("bot.logout_success", lang=lang))

    async def handle_new_conversation(self, update: Update, context):
        """Handle /new command to start new conversation."""
        user_id = str(update.effective_user.id)
        lang = self._get_user_language(user_id)
        chat_id = str(update.effective_chat.id)

        existing = (
            self.db.query(Conversation)
            .filter(
                Conversation.telegram_chat_id == chat_id,
                Conversation.bot_id == self.bot.id,
                Conversation.is_active == True,
            )
            .first()
        )
        if existing:
            existing.is_active = False
            self.db.commit()

        await update.message.reply_text(t("bot.new_conversation", lang=lang))

    async def handle_history(self, update: Update, context):
        """Handle /history command."""
        user_id = str(update.effective_user.id)
        lang = self._get_user_language(user_id)
        chat_id = str(update.effective_chat.id)

        conversations = (
            self.db.query(Conversation)
            .filter(Conversation.telegram_chat_id == chat_id, Conversation.bot_id == self.bot.id)
            .order_by(Conversation.updated_at.desc())
            .limit(5)
            .all()
        )

        if not conversations:
            await update.message.reply_text(t("bot.no_history", lang=lang))
            return

        keyboard = []
        for conv in conversations:
            status = t("conversation.status_active", lang=lang) if conv.is_active else t("conversation.status_inactive",
                                                                                         lang=lang)
            title = conv.title or f"{t('bot.untitled_conversation', lang=lang)} {conv.created_at.strftime('%Y-%m-%d %H:%M')}"
            keyboard.append(
                [InlineKeyboardButton(f"{status} {title}", callback_data=f"conv_{conv.id}")]
            )

        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(t("bot.recent_conversations", lang=lang), reply_markup=reply_markup)

    async def handle_clear(self, update: Update, context):
        """Handle /clear command."""
        user_id = str(update.effective_user.id)
        lang = self._get_user_language(user_id)
        chat_id = str(update.effective_chat.id)

        conv = (
            self.db.query(Conversation)
            .filter(
                Conversation.telegram_chat_id == chat_id,
                Conversation.bot_id == self.bot.id,
                Conversation.is_active == True,
            )
            .first()
        )
        if not conv:
            await update.message.reply_text(t("bot.nothing_to_clear", lang=lang))
            return

        self.db.query(Message).filter(Message.conversation_id == conv.id).delete()
        self.db.delete(conv)
        self.db.commit()
        await update.message.reply_text(t("bot.conversation_cleared", lang=lang))

    # ---------- CALLBACKS ----------

    async def handle_callback(self, update: Update, context):
        """Handle callback queries from inline keyboards."""
        query = update.callback_query
        await query.answer()

        user_id = str(update.effective_user.id)
        lang = self._get_user_language(user_id)

        if query.data.startswith("lang_"):
            # Language selection
            new_lang = query.data[5:]  # Extract language code
            self._set_user_language(user_id, new_lang)

            # Confirm in the new language
            confirmation = "✅ Language changed to English" if new_lang == "en" else "✅ Язык изменен на русский"
            await query.edit_message_text(confirmation)

        elif query.data.startswith("conv_"):
            conv_id = query.data[5:]
            conversation = (
                self.db.query(Conversation).filter(Conversation.id == conv_id).first()
            )

            if conversation:
                self.db.query(Conversation).filter(
                    Conversation.telegram_chat_id == conversation.telegram_chat_id,
                    Conversation.bot_id == self.bot.id,
                ).update({"is_active": False})

                conversation.is_active = True
                self.db.commit()

                title = conversation.title or t("bot.untitled_conversation", lang=lang)
                await query.edit_message_text(
                    t("bot.switched_conversation", lang=lang, title=title)
                )

    # ---------- MESSAGES (AUTH-GATED) ----------

    async def _auth_gate(self, update: Update, context) -> bool:
        """
        Returns True if the user is allowed to proceed to Dify.
        """
        if not self.bot.auth_required:
            return True

        user_id = str(update.effective_user.id)
        lang = self._get_user_language(user_id)
        text = (update.message.text or "").strip()

        # Already authenticated?
        if self._is_authenticated(user_id):
            return True

        # 6-digit code?
        if re.fullmatch(r"\d{6}", text):
            now = datetime.now(timezone.utc)
            pending_email = self.redis.get(self._pending_key(user_id))
            q = (
                self.db.query(AuthCode)
                .filter(
                    AuthCode.bot_id == self.bot.id,
                    AuthCode.is_used == False,
                    AuthCode.expires_at > now,
                    AuthCode.code == text,
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
                self._set_authenticated(user_id, code_row.email)
                self.redis.delete(self._pending_key(user_id))
                await update.message.reply_text(t("auth.success", lang=lang))
                return False
            else:
                await update.message.reply_text(t("auth.invalid_code", lang=lang))
                return False

        # Looks like email?
        if self._looks_like_email(text):
            email = text
            if not self._email_ok_for_bot(email):
                domains = ", ".join(self._allowed_domains()) or "(none configured)"
                await update.message.reply_text(
                    t("auth.email_not_allowed", lang=lang, domains=domains)
                )
                return False

            # Generate and store 6-digit code
            code = f"{secrets.randbelow(1_000_000):06d}"
            expires_at = datetime.now(timezone.utc) + timedelta(minutes=5)
            ac = AuthCode(bot_id=self.bot.id, email=email, code=code, expires_at=expires_at)
            self.db.add(ac)
            self.db.commit()

            self.redis.setex(self._pending_key(user_id), 300, email)

            try:
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

        # Not a code and not an email → prompt
        domains = self._allowed_domains()
        domains_hint = ""
        if domains:
            domains_hint = t("auth.domains_hint", lang=lang, domains=", ".join(domains))

        await update.message.reply_text(
            t("auth.required", lang=lang, domains_hint=domains_hint)
        )
        return False

    async def handle_message(self, update: Update, context):
        """Handle text messages (auth-gated before reaching Dify)."""
        if not update.message or not update.message.text:
            return

        user_id = str(update.effective_user.id)
        lang = self._get_user_language(user_id)

        # AUTH GATE
        can_proceed = await self._auth_gate(update, context)
        if not can_proceed:
            return

        chat_id = str(update.effective_chat.id)
        username = update.effective_user.username
        message_text = update.message.text

        await context.bot.send_chat_action(chat_id=chat_id, action=ChatAction.TYPING)

        # Get or create active conversation
        conversation = (
            self.db.query(Conversation)
            .filter(
                Conversation.telegram_chat_id == chat_id,
                Conversation.bot_id == self.bot.id,
                Conversation.is_active == True,
            )
            .first()
        )
        if not conversation:
            conversation = Conversation(
                bot_id=self.bot.id,
                telegram_chat_id=chat_id,
                telegram_user_id=user_id,
                telegram_username=username,
                telegram_chat_type=update.effective_chat.type,
                dify_user_id=f"telegram_{user_id}",
            )
            self.db.add(conversation)
            self.db.commit()

        # Save user message
        user_message = Message(
            conversation_id=conversation.id,
            role="user",
            content=message_text,
            telegram_message_id=str(update.message.message_id),
        )
        self.db.add(user_message)
        self.db.commit()

        response_text = ""
        message_id = None
        last_sent_text = None

        try:
            async for event in self.dify_service.send_message(
                    message=message_text,
                    conversation_id=conversation.dify_conversation_id,
                    user_id=conversation.dify_user_id,
            ):
                if event.get("event") == "message":
                    response_text += event.get("answer", "")

                    if self.bot.response_mode == "streaming":
                        if not message_id:
                            msg = await update.message.reply_text(**self._fmt(response_text, finalize=False))
                            message_id = msg.message_id
                            last_sent_text = response_text or ""
                        elif len(response_text) % 20 == 0 and response_text != last_sent_text:
                            try:
                                await context.bot.edit_message_text(
                                    chat_id=chat_id,
                                    message_id=message_id,
                                    **self._fmt(response_text, finalize=False),
                                )
                                last_sent_text = response_text
                            except BadRequest as e:
                                if "Message is not modified" not in str(e):
                                    raise

                elif event.get("event") == "message_end":
                    if not conversation.dify_conversation_id:
                        conversation.dify_conversation_id = event.get("conversation_id")

                    assistant_message = Message(
                        conversation_id=conversation.id,
                        role="assistant",
                        content=response_text,
                        dify_message_id=event.get("message_id"),
                        tokens_used=event.get("metadata", {}).get("usage", {}).get("total_tokens"),
                    )
                    self.db.add(assistant_message)
                    conversation.message_count += 2
                    conversation.last_message_at = datetime.utcnow()
                    self.db.commit()

                elif event.get("event") == "error":
                    error_msg = event.get('message', t('errors.generic_error', lang=lang))
                    await update.message.reply_text(
                        t("errors.dify_error", lang=lang, message=error_msg)
                    )
                    return

            # Final flush
            if response_text:
                if self.bot.response_mode == "blocking" or not message_id:
                    await update.message.reply_text(**self._fmt(response_text, finalize=True))
                else:
                    if response_text != (last_sent_text or ""):
                        try:
                            await context.bot.edit_message_text(
                                chat_id=chat_id,
                                message_id=message_id,
                                **self._fmt(response_text, finalize=True),
                            )
                        except BadRequest as e:
                            if "Message is not modified" not in str(e):
                                raise
            else:
                await update.message.reply_text(t("bot.no_response", lang=lang))

        except Exception as e:
            logger.error("Error handling message: %s", e)
            await update.message.reply_text(t("bot.error_occurred", lang=lang))

    async def handle_document(self, update: Update, context):
        """Handle document uploads (auth-gated)."""
        user_id = str(update.effective_user.id)
        lang = self._get_user_language(user_id)

        if self.bot.auth_required and not self._is_authenticated(user_id):
            domains = self._allowed_domains()
            domains_hint = ""
            if domains:
                domains_hint = t("auth.domains_hint", lang=lang, domains=", ".join(domains))
            await update.message.reply_text(
                t("auth.required", lang=lang, domains_hint=domains_hint)
            )
            return

        if not self.bot.enable_file_upload:
            await update.message.reply_text(t("bot.file_upload_disabled", lang=lang))
            return

        document = update.message.document
        if document.file_size > 15 * 1024 * 1024:  # 15MB limit
            await update.message.reply_text(t("bot.file_size_exceeded", lang=lang))
            return

        # Download file
        file = await context.bot.get_file(document.file_id)
        file_data = await file.download_as_bytearray()

        chat_id = str(update.effective_chat.id)
        username = update.effective_user.username
        caption = (update.message.caption or "").strip()

        # Conversation
        conversation = (
            self.db.query(Conversation)
            .filter(
                Conversation.telegram_chat_id == chat_id,
                Conversation.bot_id == self.bot.id,
                Conversation.is_active == True,
            )
            .first()
        )
        if not conversation:
            conversation = Conversation(
                bot_id=self.bot.id,
                telegram_chat_id=chat_id,
                telegram_user_id=user_id,
                telegram_username=username,
                telegram_chat_type=update.effective_chat.type,
                dify_user_id=f"telegram_{user_id}",
            )
            self.db.add(conversation)
            self.db.commit()

        # Upload to Dify
        result = await self.dify_service.upload_file(
            file_data=bytes(file_data), filename=document.file_name, user_id=f"telegram_{user_id}"
        )
        if not result:
            await update.message.reply_text(t("bot.file_upload_failed", lang=lang))
            return

        # Save a user-side message
        user_text = caption if caption else t("bot.uploaded_file", lang=lang, filename=document.file_name)
        user_message = Message(
            conversation_id=conversation.id,
            role="user",
            content=user_text,
            telegram_message_id=str(update.message.message_id),
            message_metadata={"file_name": document.file_name, "mime_type": document.mime_type},
        )
        self.db.add(user_message)
        self.db.commit()

        files_payload = [
            {"type": "document", "transfer_method": "local_file", "upload_file_id": result.get("id")}
        ]

        query_text = caption or t("bot.analyze_file", lang=lang)
        await context.bot.send_chat_action(chat_id=chat_id, action=ChatAction.TYPING)

        # Process response (similar to handle_message)
        response_text = ""
        message_id = None
        last_sent_text = None

        try:
            async for event in self.dify_service.send_message(
                    message=query_text,
                    conversation_id=conversation.dify_conversation_id,
                    user_id=conversation.dify_user_id,
                    files=files_payload,
            ):
                if event.get("event") == "message":
                    response_text += event.get("answer", "")
                    if self.bot.response_mode == "streaming":
                        if not message_id:
                            msg = await update.message.reply_text(**self._fmt(response_text, finalize=False))
                            message_id = msg.message_id
                            last_sent_text = response_text or ""
                        elif len(response_text) % 20 == 0 and response_text != last_sent_text:
                            try:
                                await context.bot.edit_message_text(
                                    chat_id=chat_id, message_id=message_id, **self._fmt(response_text, finalize=False)
                                )
                                last_sent_text = response_text
                            except BadRequest as e:
                                if "Message is not modified" not in str(e):
                                    raise

                elif event.get("event") == "message_end":
                    if not conversation.dify_conversation_id:
                        conversation.dify_conversation_id = event.get("conversation_id")

                    assistant_message = Message(
                        conversation_id=conversation.id,
                        role="assistant",
                        content=response_text,
                        dify_message_id=event.get("message_id"),
                        tokens_used=event.get("metadata", {}).get("usage", {}).get("total_tokens"),
                    )
                    self.db.add(assistant_message)
                    conversation.message_count += 2
                    conversation.last_message_at = datetime.utcnow()
                    self.db.commit()

                elif event.get("event") == "error":
                    error_msg = event.get('message', t('errors.generic_error', lang=lang))
                    await update.message.reply_text(
                        t("errors.dify_error", lang=lang, message=error_msg)
                    )
                    return

            if response_text:
                if self.bot.response_mode == "blocking" or not message_id:
                    await update.message.reply_text(**self._fmt(response_text, finalize=True))
                else:
                    if response_text != (last_sent_text or ""):
                        try:
                            await context.bot.edit_message_text(
                                chat_id=chat_id, message_id=message_id, **self._fmt(response_text, finalize=True)
                            )
                        except BadRequest as e:
                            if "Message is not modified" not in str(e):
                                raise
            else:
                await update.message.reply_text(t("bot.no_response", lang=lang))

        except Exception as e:
            logger.error("Error handling document message: %s", e)
            await update.message.reply_text(t("bot.error_occurred", lang=lang))

    async def handle_photo(self, update: Update, context):
        """Handle photo uploads (auth-gated)."""
        user_id = str(update.effective_user.id)
        lang = self._get_user_language(user_id)

        if self.bot.auth_required and not self._is_authenticated(user_id):
            domains = self._allowed_domains()
            domains_hint = ""
            if domains:
                domains_hint = t("auth.domains_hint", lang=lang, domains=", ".join(domains))
            await update.message.reply_text(
                t("auth.required", lang=lang, domains_hint=domains_hint)
            )
            return

        if not self.bot.enable_file_upload:
            await update.message.reply_text(t("bot.file_upload_disabled", lang=lang))
            return

        photo = update.message.photo[-1]  # highest resolution

        # Download photo
        file = await context.bot.get_file(photo.file_id)
        file_data = await file.download_as_bytearray()

        chat_id = str(update.effective_chat.id)
        username = update.effective_user.username
        caption = (update.message.caption or "").strip()

        # Conversation
        conversation = (
            self.db.query(Conversation)
            .filter(
                Conversation.telegram_chat_id == chat_id,
                Conversation.bot_id == self.bot.id,
                Conversation.is_active == True,
            )
            .first()
        )
        if not conversation:
            conversation = Conversation(
                bot_id=self.bot.id,
                telegram_chat_id=chat_id,
                telegram_user_id=user_id,
                telegram_username=username,
                telegram_chat_type=update.effective_chat.type,
                dify_user_id=f"telegram_{user_id}",
            )
            self.db.add(conversation)
            self.db.commit()

        # Upload to Dify
        result = await self.dify_service.upload_file(
            file_data=bytes(file_data),
            filename=f"photo_{photo.file_id}.jpg",
            user_id=f"telegram_{user_id}",
        )
        if not result:
            await update.message.reply_text(t("bot.photo_upload_failed", lang=lang))
            return

        # Save user-side message
        user_text = caption if caption else t("bot.uploaded_photo", lang=lang)
        user_message = Message(
            conversation_id=conversation.id,
            role="user",
            content=user_text,
            telegram_message_id=str(update.message.message_id),
            message_metadata={"file_name": f"photo_{photo.file_id}.jpg", "type": "image"},
        )
        self.db.add(user_message)
        self.db.commit()

        files_payload = [
            {"type": "image", "transfer_method": "local_file", "upload_file_id": result.get("id")}
        ]

        query_text = caption or t("bot.analyze_image", lang=lang)
        await context.bot.send_chat_action(chat_id=chat_id, action=ChatAction.TYPING)

        # Process response
        response_text = ""
        message_id = None
        last_sent_text = None

        try:
            async for event in self.dify_service.send_message(
                    message=query_text,
                    conversation_id=conversation.dify_conversation_id,
                    user_id=conversation.dify_user_id,
                    files=files_payload,
            ):
                if event.get("event") == "message":
                    response_text += event.get("answer", "")
                    if self.bot.response_mode == "streaming":
                        if not message_id:
                            msg = await update.message.reply_text(**self._fmt(response_text, finalize=False))
                            message_id = msg.message_id
                            last_sent_text = response_text or ""
                        elif len(response_text) % 20 == 0 and response_text != last_sent_text:
                            try:
                                await context.bot.edit_message_text(
                                    chat_id=chat_id, message_id=message_id, **self._fmt(response_text, finalize=False)
                                )
                                last_sent_text = response_text
                            except BadRequest as e:
                                if "Message is not modified" not in str(e):
                                    raise

                elif event.get("event") == "message_end":
                    if not conversation.dify_conversation_id:
                        conversation.dify_conversation_id = event.get("conversation_id")
                    assistant_message = Message(
                        conversation_id=conversation.id,
                        role="assistant",
                        content=response_text,
                        dify_message_id=event.get("message_id"),
                        tokens_used=event.get("metadata", {}).get("usage", {}).get("total_tokens"),
                    )
                    self.db.add(assistant_message)
                    conversation.message_count += 2
                    conversation.last_message_at = datetime.utcnow()
                    self.db.commit()

                elif event.get("event") == "error":
                    error_msg = event.get('message', t('errors.generic_error', lang=lang))
                    await update.message.reply_text(
                        t("errors.dify_error", lang=lang, message=error_msg)
                    )
                    return

            if response_text:
                if self.bot.response_mode == "blocking" or not message_id:
                    await update.message.reply_text(**self._fmt(response_text, finalize=True))
                else:
                    if response_text != (last_sent_text or ""):
                        try:
                            await context.bot.edit_message_text(
                                chat_id=chat_id, message_id=message_id, **self._fmt(response_text, finalize=True)
                            )
                        except BadRequest as e:
                            if "Message is not modified" not in str(e):
                                raise
            else:
                await update.message.reply_text(t("bot.no_response", lang=lang))

        except Exception as e:
            logger.error("Error handling photo message: %s", e)
            await update.message.reply_text(t("bot.error_occurred", lang=lang))
