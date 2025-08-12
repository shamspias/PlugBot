"""Markdown formatting utilities for Telegram messages."""

from telegram import Update
from telegram.constants import ParseMode
from telegram.error import BadRequest
from telegram.ext import ContextTypes

from ....utils.logger import get_logger

logger = get_logger(__name__)


class MarkdownFormatter:
    """Handles markdown formatting for Telegram messages."""

    def __init__(self, bot):
        self.bot = bot

    def escape_all_markdown(self, text: str) -> str:
        """Escape ALL MarkdownV2 special characters for safe plain text."""
        if not text:
            return text

        special_chars = r"_*[]()~`>#+-=|{}.!\\"
        escaped = ""
        for char in text:
            if char in special_chars:
                escaped += f"\\{char}"
            else:
                escaped += char
        return escaped

    def validate_markdown(self, text: str) -> bool:
        """Validate if markdown formatting is properly formed."""
        if not text:
            return True

        try:
            # Check for balanced bold markers
            bold_count = text.count('**')
            if bold_count % 2 != 0:
                return False

            # Check for balanced italic markers
            italic_count = 0
            i = 0
            while i < len(text):
                if text[i] == '_' and (i == 0 or text[i - 1] != '\\'):
                    italic_count += 1
                i += 1

            if italic_count % 2 != 0:
                return False

            # Check for balanced code markers
            code_count = text.count('`')
            if code_count % 2 != 0:
                return False

            # Check for other paired markers
            paired_markers = ['[]', '()', '{}']
            for open_char, close_char in paired_markers:
                open_count = text.count(open_char)
                close_count = text.count(close_char)
                if open_count != close_count:
                    return False

            return True

        except Exception:
            return False

    def sanitize_markdown(self, text: str) -> str:
        """Attempt to fix common markdown issues."""
        if not text:
            return text

        # Remove incomplete bold formatting
        bold_parts = text.split('**')
        if len(bold_parts) % 2 == 0:  # Even number of parts means odd number of **
            text = '**'.join(bold_parts[:-1]) + bold_parts[-1]

        # Handle incomplete italic formatting
        italic_parts = []
        current_part = ""
        in_italic = False

        i = 0
        while i < len(text):
            if text[i] == '_' and (i == 0 or text[i - 1] != '\\'):
                if in_italic:
                    italic_parts.append(current_part + '_')
                    current_part = ""
                    in_italic = False
                else:
                    if current_part:
                        italic_parts.append(current_part)
                    current_part = '_'
                    in_italic = True
            else:
                current_part += text[i]
            i += 1

        if current_part:
            italic_parts.append(current_part)

        text = ''.join(italic_parts)

        return text

    def escape_markdown_safely(self, text: str) -> str:
        """Safely escape markdown, preserving valid formatting and escaping invalid parts."""
        if not text:
            return text

        # First, try to sanitize the markdown
        sanitized = self.sanitize_markdown(text)

        # If after sanitization it's still invalid, escape everything
        if not self.validate_markdown(sanitized):
            return self.escape_all_markdown(text)

        # If valid, do minimal escaping preserving * and _
        specials_to_escape = r"[]()~`>#+-=|{}.!\\"
        out = []
        for ch in sanitized:
            if ch in specials_to_escape:
                out.append("\\" + ch)
            else:
                out.append(ch)
        return "".join(out)

    def format_text(self, text: str, finalize: bool = False) -> dict:
        """Format text with appropriate markdown settings."""
        use_md = bool(getattr(self.bot, "telegram_markdown_enabled", False))
        safe_text = text if (text is not None and text != "") else "…"

        if not use_md:
            return {"text": safe_text}

        if finalize:
            try:
                # Attempt to use markdown with validation
                if self.validate_markdown(safe_text):
                    escaped_text = self.escape_markdown_safely(safe_text)
                    return {
                        "text": escaped_text,
                        "parse_mode": ParseMode.MARKDOWN_V2,
                    }
                else:
                    # Fallback to escaped plain text if markdown is invalid
                    logger.warning(f"Invalid markdown detected, falling back to plain text for bot {self.bot.name}")
                    return {
                        "text": self.escape_all_markdown(safe_text),
                        "parse_mode": ParseMode.MARKDOWN_V2,
                    }
            except Exception as e:
                # Ultimate fallback: plain text without parse mode
                logger.error(f"Markdown processing failed for bot {self.bot.name}: {e}")
                return {"text": safe_text}

        return {"text": safe_text}

    async def send_message_safely(self, update: Update, context: ContextTypes.DEFAULT_TYPE,
                                  chat_id, message_id, text, is_edit=False):
        """Safely send or edit a message with fallback handling for markdown errors."""
        try:
            fmt_result = self.format_text(text, finalize=True)

            if is_edit:
                await context.bot.edit_message_text(
                    chat_id=chat_id,
                    message_id=message_id,
                    **fmt_result
                )
            else:
                return await update.message.reply_text(**fmt_result)

        except BadRequest as e:
            error_msg = str(e).lower()

            # Handle markdown parsing errors
            if any(keyword in error_msg for keyword in ["can't parse", "entities", "markdown", "bold", "italic"]):
                logger.warning(f"Markdown parsing failed for bot {self.bot.name}, falling back to plain text: {e}")

                # Fallback to plain text
                try:
                    if is_edit:
                        await context.bot.edit_message_text(
                            chat_id=chat_id,
                            message_id=message_id,
                            text=text  # Send as plain text without parse_mode
                        )
                    else:
                        return await update.message.reply_text(text)

                except BadRequest as e2:
                    # If even plain text fails, log and skip
                    if "Message is not modified" not in str(e2):
                        logger.error(f"Failed to send even plain text message: {e2}")
                        raise
            else:
                # Re-raise non-markdown errors
                if "Message is not modified" not in error_msg:
                    raise
