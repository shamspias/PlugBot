from typing import Dict, Any, Optional
from ..core.config import settings
import json
from pathlib import Path


class I18nManager:
    """Internationalization manager for handling translations."""

    _instance = None
    _translations: Dict[str, Dict[str, Any]] = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._load_translations()
        return cls._instance

    def _load_translations(self):
        """Load all translation files from the translations directory."""
        translations_dir = Path(__file__).parent / "translations"

        # Load English translations
        en_path = translations_dir / "en.json"
        if en_path.exists():
            with open(en_path, 'r', encoding='utf-8') as f:
                self._translations['en'] = json.load(f)

        # Load Russian translations
        ru_path = translations_dir / "ru.json"
        if ru_path.exists():
            with open(ru_path, 'r', encoding='utf-8') as f:
                self._translations['ru'] = json.load(f)

    def get(self, key: str, lang: Optional[str] = None, **kwargs) -> str:
        """
        Get translated text for the given key.

        Args:
            key: Translation key (e.g., "welcome.message")
            lang: Language code (e.g., "en", "ru"). If None, uses default from settings
            **kwargs: Variables to format in the translation string

        Returns:
            Translated string
        """
        if lang is None:
            lang = settings.DEFAULT_LANGUAGE

        # Fallback to English if language not found
        if lang not in self._translations:
            lang = 'en'

        # Navigate through nested keys (e.g., "welcome.message")
        keys = key.split('.')
        value = self._translations.get(lang, {})

        for k in keys:
            if isinstance(value, dict):
                value = value.get(k, None)
            else:
                value = None
                break

        # If key not found, fallback to English
        if value is None and lang != 'en':
            value = self._translations.get('en', {})
            for k in keys:
                if isinstance(value, dict):
                    value = value.get(k, None)
                else:
                    value = None
                    break

        # If still not found, return the key itself
        if value is None:
            return f"[{key}]"

        # Format the string with provided kwargs
        if kwargs:
            try:
                return value.format(**kwargs)
            except (KeyError, ValueError):
                return value

        return value

    def get_available_languages(self) -> Dict[str, str]:
        """Get list of available languages."""
        return {
            'en': 'English',
            'ru': 'Русский'
        }

    def is_language_supported(self, lang: str) -> bool:
        """Check if a language is supported."""
        return lang in self._translations


# Global instance
i18n = I18nManager()


# Helper function for convenience
def t(key: str, lang: Optional[str] = None, **kwargs) -> str:
    """
    Translate helper function.

    Usage:
        t("welcome.message", name="John")
        t("errors.not_found", lang="ru")
    """
    return i18n.get(key, lang, **kwargs)
