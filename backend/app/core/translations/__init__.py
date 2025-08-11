"""
Translations module for PlugBot.

This module contains all translation files for supported languages.
To add a new language:
1. Create a new JSON file with the language code (e.g., 'de.json' for German)
2. Follow the same structure as en.json
3. Update the supported languages in config.py
"""

from pathlib import Path

TRANSLATIONS_DIR = Path(__file__).parent


# List all available translation files
def get_available_translations():
    """Get list of available translation files."""
    translations = []
    for file in TRANSLATIONS_DIR.glob("*.json"):
        if file.stem != "__init__":
            translations.append(file.stem)
    return translations


# Validate translation files on import
def validate_translations():
    """Validate that essential translation files exist."""
    required = ["en.json", "ru.json"]
    for file in required:
        path = TRANSLATIONS_DIR / file
        if not path.exists():
            raise FileNotFoundError(f"Required translation file missing: {file}")


# Run validation when module is imported
validate_translations()
