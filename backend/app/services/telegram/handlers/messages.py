"""Message handlers for Telegram bot."""

from datetime import datetime
from telegram import Update
from telegram.constants import ChatAction
from telegram.ext import ContextTypes

from ....core.i18n import t
from ....models.conversation import Conversation, Message
from ....utils.logger import get_logger
from ..utils.markdown import MarkdownFormatter

logger = get_logger(__name__)


class MessageHandlers:
    """Handles all message-related operations."""

    def __init__(self, telegram_service):
        self.service = telegram_service
        self.bot = telegram_service.bot
        self.db = telegram_service.db
        self.dify_service = telegram_service.dify_service
        self.auth_manager = telegram_service.auth_manager
        self.language_manager = telegram_service.language_manager
        self.markdown_formatter = MarkdownFormatter(telegram_service.bot)

    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle text messages (auth-gated before reaching Dify)."""
        if not update.message or not update.message.text:
            return

        user_id = str(update.effective_user.id)
        lang = self.language_manager.get_user_language(user_id)

        # Check authentication
        can_proceed = await self.auth_manager.auth_gate(update, context, lang)
        if not can_proceed:
            return

        chat_id = str(update.effective_chat.id)
        username = update.effective_user.username
        message_text = update.message.text

        await context.bot.send_chat_action(chat_id=chat_id, action=ChatAction.TYPING)

        # Get or create conversation
        conversation = self._get_or_create_conversation(chat_id, user_id, username, update.effective_chat.type)

        # Save user message
        user_message = Message(
            conversation_id=conversation.id,
            role="user",
            content=message_text,
            telegram_message_id=str(update.message.message_id),
        )
        self.db.add(user_message)
        self.db.commit()

        # Process with Dify
        await self._process_dify_response(
            update, context, conversation, message_text, lang
        )

    async def handle_document(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle document uploads (auth-gated)."""
        user_id = str(update.effective_user.id)
        lang = self.language_manager.get_user_language(user_id)

        # Check authentication
        if self.bot.auth_required and not self.auth_manager.is_authenticated(user_id):
            domains = self.auth_manager.get_allowed_domains()
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

        # Download and process file
        await self._process_file_upload(update, context, document, lang, "document")

    async def handle_photo(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle photo uploads (auth-gated)."""
        user_id = str(update.effective_user.id)
        lang = self.language_manager.get_user_language(user_id)

        # Check authentication
        if self.bot.auth_required and not self.auth_manager.is_authenticated(user_id):
            domains = self.auth_manager.get_allowed_domains()
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

        # Process photo upload
        await self._process_file_upload(update, context, photo, lang, "photo")

    def _get_or_create_conversation(self, chat_id: str, user_id: str, username: str, chat_type: str) -> Conversation:
        """Get or create active conversation."""
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
                telegram_chat_type=chat_type,
                dify_user_id=f"telegram_{user_id}",
            )
            self.db.add(conversation)
            self.db.commit()

        return conversation

    async def _process_dify_response(self, update, context, conversation, message_text, lang):
        """Process response from Dify service."""
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
                            msg = await self.markdown_formatter.send_message_safely(
                                update, context,
                                update.effective_chat.id, None,
                                response_text, is_edit=False
                            )
                            if msg:
                                message_id = msg.message_id
                            last_sent_text = response_text or ""
                        elif len(response_text) % 20 == 0 and response_text != last_sent_text:
                            await self.markdown_formatter.send_message_safely(
                                update, context,
                                update.effective_chat.id, message_id,
                                response_text, is_edit=True
                            )
                            last_sent_text = response_text

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
                    await self.markdown_formatter.send_message_safely(
                        update, context,
                        update.effective_chat.id, None,
                        response_text, is_edit=False
                    )
                else:
                    if response_text != (last_sent_text or ""):
                        await self.markdown_formatter.send_message_safely(
                            update, context,
                            update.effective_chat.id, message_id,
                            response_text, is_edit=True
                        )
            else:
                await update.message.reply_text(t("bot.no_response", lang=lang))

        except Exception as e:
            logger.error("Error handling message: %s", e)
            await update.message.reply_text(t("bot.error_occurred", lang=lang))

    async def _process_file_upload(self, update, context, file_obj, lang, file_type):
        """Process file upload to Dify."""
        chat_id = str(update.effective_chat.id)
        user_id = str(update.effective_user.id)
        username = update.effective_user.username
        caption = (update.message.caption or "").strip()

        # Download file
        if file_type == "document":
            file = await context.bot.get_file(file_obj.file_id)
            filename = file_obj.file_name
            upload_type = "document"
        else:  # photo
            file = await context.bot.get_file(file_obj.file_id)
            filename = f"photo_{file_obj.file_id}.jpg"
            upload_type = "image"

        file_data = await file.download_as_bytearray()

        # Get conversation
        conversation = self._get_or_create_conversation(
            chat_id, user_id, username, update.effective_chat.type
        )

        # Upload to Dify
        result = await self.dify_service.upload_file(
            file_data=bytes(file_data),
            filename=filename,
            user_id=f"telegram_{user_id}"
        )

        if not result:
            error_key = f"bot.{file_type}_upload_failed"
            await update.message.reply_text(t(error_key, lang=lang))
            return

        # Save user message
        if file_type == "document":
            user_text = caption if caption else t("bot.uploaded_file", lang=lang, filename=filename)
        else:
            user_text = caption if caption else t("bot.uploaded_photo", lang=lang)

        user_message = Message(
            conversation_id=conversation.id,
            role="user",
            content=user_text,
            telegram_message_id=str(update.message.message_id),
            message_metadata={"file_name": filename, "type": upload_type},
        )
        self.db.add(user_message)
        self.db.commit()

        # Prepare file payload
        files_payload = [
            {"type": upload_type, "transfer_method": "local_file", "upload_file_id": result.get("id")}
        ]

        # Determine query text
        if file_type == "document":
            query_text = caption or t("bot.analyze_file", lang=lang)
        else:
            query_text = caption or t("bot.analyze_image", lang=lang)

        await context.bot.send_chat_action(chat_id=chat_id, action=ChatAction.TYPING)

        # Process response
        await self._process_dify_response_with_files(
            update, context, conversation, query_text, files_payload, lang
        )

    async def _process_dify_response_with_files(self, update, context, conversation, query_text, files, lang):
        """Process Dify response with file attachments."""
        response_text = ""
        message_id = None
        last_sent_text = None

        try:
            async for event in self.dify_service.send_message(
                    message=query_text,
                    conversation_id=conversation.dify_conversation_id,
                    user_id=conversation.dify_user_id,
                    files=files,
            ):
                if event.get("event") == "message":
                    response_text += event.get("answer", "")

                    if self.bot.response_mode == "streaming":
                        if not message_id:
                            msg = await self.markdown_formatter.send_message_safely(
                                update, context,
                                update.effective_chat.id, None,
                                response_text, is_edit=False
                            )
                            if msg:
                                message_id = msg.message_id
                            last_sent_text = response_text or ""
                        elif len(response_text) % 20 == 0 and response_text != last_sent_text:
                            await self.markdown_formatter.send_message_safely(
                                update, context,
                                update.effective_chat.id, message_id,
                                response_text, is_edit=True
                            )
                            last_sent_text = response_text

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
                    await self.markdown_formatter.send_message_safely(
                        update, context,
                        update.effective_chat.id, None,
                        response_text, is_edit=False
                    )
                else:
                    if response_text != (last_sent_text or ""):
                        await self.markdown_formatter.send_message_safely(
                            update, context,
                            update.effective_chat.id, message_id,
                            response_text, is_edit=True
                        )
            else:
                await update.message.reply_text(t("bot.no_response", lang=lang))

        except Exception as e:
            logger.error("Error handling file message: %s", e)
            await update.message.reply_text(t("bot.error_occurred", lang=lang))
