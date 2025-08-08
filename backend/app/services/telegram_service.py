from telegram import Update, Bot as TelegramBot, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackQueryHandler
from telegram.constants import ParseMode, ChatAction
import asyncio
from typing import Optional, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session
from ..models.bot import Bot
from ..models.conversation import Conversation, Message
from ..core.security import security_manager
from ..services.dify_service import DifyService
from ..utils.logger import get_logger

logger = get_logger(__name__)


class TelegramService:
    """Service for managing Telegram bot integration."""

    def __init__(self, bot: Bot, db: Session):
        self.bot = bot
        self.db = db
        self.token = security_manager.decrypt_data(bot.telegram_bot_token)
        self.application: Optional[Application] = None
        self.dify_service = DifyService(bot)
        self.running = False

    async def initialize(self):
        """Initialize Telegram bot."""
        try:
            self.application = Application.builder().token(self.token).build()

            # Add handlers
            self.application.add_handler(CommandHandler("start", self.handle_start))
            self.application.add_handler(CommandHandler("help", self.handle_help))
            self.application.add_handler(CommandHandler("new", self.handle_new_conversation))
            self.application.add_handler(CommandHandler("history", self.handle_history))
            self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))
            self.application.add_handler(MessageHandler(filters.Document.ALL, self.handle_document))
            self.application.add_handler(MessageHandler(filters.PHOTO, self.handle_photo))
            self.application.add_handler(CallbackQueryHandler(self.handle_callback))

            # Initialize bot
            await self.application.initialize()
            await self.application.bot.set_my_commands([
                ("start", "Start the bot"),
                ("help", "Show help message"),
                ("new", "Start new conversation"),
                ("history", "Show conversation history")
            ])

            self.running = True
            logger.info(f"Telegram bot {self.bot.name} initialized successfully")
            return True

        except Exception as e:
            logger.error(f"Failed to initialize Telegram bot: {str(e)}")
            return False

    async def start_polling(self):
        """Start polling for updates."""
        if self.application and not self.running:
            await self.application.start()
            await self.application.updater.start_polling(drop_pending_updates=True)
            self.running = True
            logger.info(f"Started polling for bot {self.bot.name}")

    async def stop(self):
        """Stop the bot."""
        if self.application and self.running:
            await self.application.updater.stop()
            await self.application.stop()
            await self.application.shutdown()
            self.running = False
            logger.info(f"Stopped bot {self.bot.name}")

    async def handle_start(self, update: Update, context):
        """Handle /start command."""
        welcome_message = (
            f"🤖 Welcome to {self.bot.name}!\n\n"
            f"{self.bot.description or 'I am your AI assistant powered by Dify.'}\n\n"
            "Commands:\n"
            "/help - Show this help message\n"
            "/new - Start a new conversation\n"
            "/history - Show recent conversations\n\n"
            "Just send me a message to start chatting!"
        )
        await update.message.reply_text(welcome_message, parse_mode=ParseMode.MARKDOWN)

    async def handle_help(self, update: Update, context):
        """Handle /help command."""
        await self.handle_start(update, context)

    async def handle_new_conversation(self, update: Update, context):
        """Handle /new command to start new conversation."""
        chat_id = str(update.effective_chat.id)
        user_id = str(update.effective_user.id)

        # Deactivate existing conversation
        existing = self.db.query(Conversation).filter(
            Conversation.telegram_chat_id == chat_id,
            Conversation.bot_id == self.bot.id,
            Conversation.is_active == True
        ).first()

        if existing:
            existing.is_active = False
            self.db.commit()

        await update.message.reply_text("✨ Started a new conversation. Send me your message!")

    async def handle_history(self, update: Update, context):
        """Handle /history command."""
        chat_id = str(update.effective_chat.id)

        conversations = self.db.query(Conversation).filter(
            Conversation.telegram_chat_id == chat_id,
            Conversation.bot_id == self.bot.id
        ).order_by(Conversation.updated_at.desc()).limit(5).all()

        if not conversations:
            await update.message.reply_text("No conversation history found.")
            return

        keyboard = []
        for conv in conversations:
            status = "🟢" if conv.is_active else "⚪"
            title = conv.title or f"Conversation {conv.created_at.strftime('%Y-%m-%d %H:%M')}"
            keyboard.append([
                InlineKeyboardButton(
                    f"{status} {title}",
                    callback_data=f"conv_{conv.id}"
                )
            ])

        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(
            "📚 Recent Conversations:",
            reply_markup=reply_markup
        )

    async def handle_message(self, update: Update, context):
        """Handle text messages."""
        if not update.message or not update.message.text:
            return

        chat_id = str(update.effective_chat.id)
        user_id = str(update.effective_user.id)
        username = update.effective_user.username
        message_text = update.message.text

        # Send typing action
        await context.bot.send_chat_action(chat_id=chat_id, action=ChatAction.TYPING)

        # Get or create conversation
        conversation = self.db.query(Conversation).filter(
            Conversation.telegram_chat_id == chat_id,
            Conversation.bot_id == self.bot.id,
            Conversation.is_active == True
        ).first()

        if not conversation:
            conversation = Conversation(
                bot_id=self.bot.id,
                telegram_chat_id=chat_id,
                telegram_user_id=user_id,
                telegram_username=username,
                telegram_chat_type=update.effective_chat.type,
                dify_user_id=f"telegram_{user_id}"
            )
            self.db.add(conversation)
            self.db.commit()

        # Save user message
        user_message = Message(
            conversation_id=conversation.id,
            role="user",
            content=message_text,
            telegram_message_id=str(update.message.message_id)
        )
        self.db.add(user_message)
        self.db.commit()

        # Send message to Dify
        response_text = ""
        message_id = None

        try:
            async for event in self.dify_service.send_message(
                    message=message_text,
                    conversation_id=conversation.dify_conversation_id,
                    user_id=conversation.dify_user_id
            ):
                if event.get("event") == "message":
                    response_text += event.get("answer", "")

                    # Update message in real-time for streaming
                    if self.bot.response_mode == "streaming":
                        if not message_id:
                            msg = await update.message.reply_text(response_text or "...")
                            message_id = msg.message_id
                        elif len(response_text) % 20 == 0:  # Update every 20 chars
                            try:
                                await context.bot.edit_message_text(
                                    chat_id=chat_id,
                                    message_id=message_id,
                                    text=response_text
                                )
                            except:
                                pass

                elif event.get("event") == "message_end":
                    # Update conversation ID if first message
                    if not conversation.dify_conversation_id:
                        conversation.dify_conversation_id = event.get("conversation_id")

                    # Save assistant message
                    assistant_message = Message(
                        conversation_id=conversation.id,
                        role="assistant",
                        content=response_text,
                        dify_message_id=event.get("message_id"),
                        tokens_used=event.get("metadata", {}).get("usage", {}).get("total_tokens")
                    )
                    self.db.add(assistant_message)

                    # Update conversation
                    conversation.message_count += 2
                    conversation.last_message_at = datetime.utcnow()
                    self.db.commit()

                elif event.get("event") == "error":
                    error_msg = event.get("message", "An error occurred")
                    await update.message.reply_text(f"❌ {error_msg}")
                    return

            # Send final message if not streaming or update final
            if response_text:
                if self.bot.response_mode == "blocking" or not message_id:
                    await update.message.reply_text(response_text)
                else:
                    await context.bot.edit_message_text(
                        chat_id=chat_id,
                        message_id=message_id,
                        text=response_text
                    )
            else:
                await update.message.reply_text("I couldn't generate a response. Please try again.")

        except Exception as e:
            logger.error(f"Error handling message: {str(e)}")
            await update.message.reply_text("❌ An error occurred. Please try again.")

    async def handle_document(self, update: Update, context):
        """Handle document uploads."""
        if not self.bot.enable_file_upload:
            await update.message.reply_text("File uploads are disabled for this bot.")
            return

        document = update.message.document
        if document.file_size > 15 * 1024 * 1024:  # 15MB limit
            await update.message.reply_text("File size exceeds 15MB limit.")
            return

        # Download file
        file = await context.bot.get_file(document.file_id)
        file_data = await file.download_as_bytearray()

        # Upload to Dify
        chat_id = str(update.effective_chat.id)
        user_id = str(update.effective_user.id)

        result = await self.dify_service.upload_file(
            file_data=bytes(file_data),
            filename=document.file_name,
            user_id=f"telegram_{user_id}"
        )

        if result:
            await update.message.reply_text(
                f"✅ File '{document.file_name}' uploaded successfully. "
                "You can now ask questions about it."
            )
        else:
            await update.message.reply_text("❌ Failed to upload file.")

    async def handle_photo(self, update: Update, context):
        """Handle photo uploads."""
        if not self.bot.enable_file_upload:
            await update.message.reply_text("File uploads are disabled for this bot.")
            return

        photo = update.message.photo[-1]  # Get highest resolution

        # Download photo
        file = await context.bot.get_file(photo.file_id)
        file_data = await file.download_as_bytearray()

        # Upload to Dify
        chat_id = str(update.effective_chat.id)
        user_id = str(update.effective_user.id)

        result = await self.dify_service.upload_file(
            file_data=bytes(file_data),
            filename=f"photo_{photo.file_id}.jpg",
            user_id=f"telegram_{user_id}"
        )

        if result:
            await update.message.reply_text(
                "✅ Photo uploaded successfully. You can now ask questions about it."
            )
        else:
            await update.message.reply_text("❌ Failed to upload photo.")

    async def handle_callback(self, update: Update, context):
        """Handle callback queries from inline keyboards."""
        query = update.callback_query
        await query.answer()

        if query.data.startswith("conv_"):
            conv_id = query.data[5:]
            conversation = self.db.query(Conversation).filter(
                Conversation.id == conv_id
            ).first()

            if conversation:
                # Activate this conversation
                self.db.query(Conversation).filter(
                    Conversation.telegram_chat_id == conversation.telegram_chat_id,
                    Conversation.bot_id == self.bot.id
                ).update({"is_active": False})

                conversation.is_active = True
                self.db.commit()

                await query.edit_message_text(
                    f"✅ Switched to conversation: {conversation.title or 'Untitled'}"
                )
