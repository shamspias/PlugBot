"""
Backward compatibility wrapper for the refactored telegram service.
This allows existing code to continue working without changes.
"""
from .telegram import TelegramService

__all__ = ['TelegramService']
