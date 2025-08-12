"""Command handlers for Telegram bot."""

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode
from telegram.ext import ContextTypes

from ....core.i18n import t
from ....models.conversation import Conversation
from ....utils.logger import get_logger

logger = get_logger(__name__)


class CommandHandlers:
    """Handles all command-related operations."""

    def __init__(self, telegram_service):
        self.service = telegram_service
        self.bot = telegram_service.bot
        self.db = telegram_service.db
        self.language_manager = telegram_service.language_manager
        self.auth_manager = telegram_service.auth_manager

    async def handle_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command."""
        user_id = str(update.effective_user.id)
        lang = self.language_manager.get_user_language(user_id)

        if self.bot.description:
            welcome_message = t("bot.welcome", lang=lang,
                                bot_name=self.bot.name,
                                description=self.bot.description)
        else:
            welcome_message = t("bot.welcome_no_desc", lang=lang,
                                bot_name=self.bot.name)

        await update.message.reply_text(welcome_message, parse_mode=ParseMode.MARKDOWN)

    async def handle_help(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /help command."""
        await self.handle_start(update, context)

    async def handle_language(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /language command to change user's language preference."""
        keyboard = [
            [
                InlineKeyboardButton("🇬🇧 English", callback_data="lang_en"),
                InlineKeyboardButton("🇷🇺 Русский", callback_data="lang_ru")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        msg_text = "Choose your language / Выберите язык:"
        await update.message.reply_text(msg_text, reply_markup=reply_markup)

    async def handle_logout(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /logout command."""
        user_id = str(update.effective_user.id)
        lang = self.language_manager.get_user_language(user_id)

        self.auth_manager.clear_authenticated(user_id)
        await update.message.reply_text(t("bot.logout_success", lang=lang))

    async def handle_new_conversation(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /new command to start new conversation."""
        user_id = str(update.effective_user.id)
        lang = self.language_manager.get_user_language(user_id)
        chat_id = str(update.effective_chat.id)

        # Deactivate existing conversation
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

    async def handle_history(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /history command."""
        user_id = str(update.effective_user.id)
        lang = self.language_manager.get_user_language(user_id)
        chat_id = str(update.effective_chat.id)

        conversations = (
            self.db.query(Conversation)
            .filter(
                Conversation.telegram_chat_id == chat_id,
                Conversation.bot_id == self.bot.id
            )
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

    async def handle_clear(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /clear command."""
        user_id = str(update.effective_user.id)
        lang = self.language_manager.get_user_language(user_id)
        chat_id = str(update.effective_chat.id)

        from ....models.conversation import Message

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
