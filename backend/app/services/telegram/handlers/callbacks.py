"""Callback query handlers for Telegram bot."""

from telegram import Update
from telegram.ext import ContextTypes

from ....core.i18n import t
from ....models.conversation import Conversation
from ....utils.logger import get_logger

logger = get_logger(__name__)


class CallbackHandlers:
    """Handles all callback query operations."""

    def __init__(self, telegram_service):
        self.service = telegram_service
        self.bot = telegram_service.bot
        self.db = telegram_service.db
        self.language_manager = telegram_service.language_manager

    async def handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle callback queries from inline keyboards."""
        query = update.callback_query
        await query.answer()

        user_id = str(update.effective_user.id)
        lang = self.language_manager.get_user_language(user_id)

        if query.data.startswith("lang_"):
            await self._handle_language_selection(query, user_id)
        elif query.data.startswith("conv_"):
            await self._handle_conversation_selection(query, user_id, lang)

    async def _handle_language_selection(self, query, user_id: str):
        """Handle language selection callback."""
        new_lang = query.data[5:]  # Extract language code
        self.language_manager.set_user_language(user_id, new_lang)

        # Confirm in the new language
        confirmation = "✅ Language changed to English" if new_lang == "en" else "✅ Язык изменен на русский"
        await query.edit_message_text(confirmation)

    async def _handle_conversation_selection(self, query, user_id: str, lang: str):
        """Handle conversation selection callback."""
        conv_id = query.data[5:]
        conversation = (
            self.db.query(Conversation).filter(Conversation.id == conv_id).first()
        )

        if conversation:
            # Deactivate all conversations for this chat
            self.db.query(Conversation).filter(
                Conversation.telegram_chat_id == conversation.telegram_chat_id,
                Conversation.bot_id == self.bot.id,
            ).update({"is_active": False})

            # Activate selected conversation
            conversation.is_active = True
            self.db.commit()

            title = conversation.title or t("bot.untitled_conversation", lang=lang)
            await query.edit_message_text(
                t("bot.switched_conversation", lang=lang, title=title)
            )
