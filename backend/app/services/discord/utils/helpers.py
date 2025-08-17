"""Helper utilities for Discord bot."""

from ....core.security import security_manager
from ....utils.logger import get_logger

logger = get_logger(__name__)


class DiscordHelpers:
    """General helper functions for Discord bot operations."""

    @staticmethod
    def decrypt_token(encrypted_token: str) -> str:
        """Decrypt bot token."""
        return security_manager.decrypt_data(encrypted_token)

    @staticmethod
    def format_embed_description(text: str, max_length: int = 4000) -> str:
        """Format text for Discord embed description."""
        if len(text) <= max_length:
            return text

        # Truncate and add ellipsis
        return text[:max_length - 3] + "..."

    @staticmethod
    def split_long_message(text: str, max_length: int = 4000) -> list:
        """Split long message into chunks for Discord."""
        if len(text) <= max_length:
            return [text]

        chunks = []
        while text:
            # Try to split at a newline or space
            chunk = text[:max_length]

            if len(text) > max_length:
                # Find last newline or space
                last_newline = chunk.rfind('\n')
                last_space = chunk.rfind(' ')

                if last_newline > max_length * 0.8:
                    chunk = chunk[:last_newline]
                elif last_space > max_length * 0.8:
                    chunk = chunk[:last_space]

            chunks.append(chunk)
            text = text[len(chunk):].lstrip()

        return chunks
