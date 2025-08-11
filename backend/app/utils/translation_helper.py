"""
Utility functions for managing translations in PlugBot.
This module provides helpers for adding new languages and validating translations.
"""

import json
from pathlib import Path
from typing import Dict, Any, List, Set
from ..core.config import settings


class TranslationValidator:
    """Validate and manage translation files."""

    def __init__(self):
        self.translations_dir = Path(__file__).parent.parent / "core" / "translations"

    def get_all_keys(self, data: Dict, prefix: str = "") -> Set[str]:
        """Recursively get all translation keys from a dictionary."""
        keys = set()
        for key, value in data.items():
            full_key = f"{prefix}.{key}" if prefix else key
            if isinstance(value, dict):
                keys.update(self.get_all_keys(value, full_key))
            else:
                keys.add(full_key)
        return keys

    def validate_language_file(self, lang_code: str) -> Dict[str, Any]:
        """
        Validate a language file against the English reference.
        Returns dict with missing and extra keys.
        """
        # Load English reference
        en_path = self.translations_dir / "en.json"
        with open(en_path, 'r', encoding='utf-8') as f:
            en_data = json.load(f)
        en_keys = self.get_all_keys(en_data)

        # Load target language
        lang_path = self.translations_dir / f"{lang_code}.json"
        if not lang_path.exists():
            return {"error": f"Language file {lang_code}.json not found"}

        with open(lang_path, 'r', encoding='utf-8') as f:
            lang_data = json.load(f)
        lang_keys = self.get_all_keys(lang_data)

        # Find differences
        missing_keys = en_keys - lang_keys
        extra_keys = lang_keys - en_keys

        return {
            "language": lang_code,
            "total_keys": len(en_keys),
            "translated_keys": len(lang_keys & en_keys),
            "missing_keys": list(missing_keys),
            "extra_keys": list(extra_keys),
            "completion_percentage": round(len(lang_keys & en_keys) / len(en_keys) * 100, 2)
        }

    def create_language_template(self, lang_code: str, lang_name: str) -> bool:
        """
        Create a new language file template based on English.

        Args:
            lang_code: Language code (e.g., 'de' for German)
            lang_name: Language name for comments
        """
        en_path = self.translations_dir / "en.json"
        new_path = self.translations_dir / f"{lang_code}.json"

        if new_path.exists():
            print(f"Language file {lang_code}.json already exists")
            return False

        with open(en_path, 'r', encoding='utf-8') as f:
            template = json.load(f)

        # Add placeholder comment at the top level
        def add_placeholders(data):
            """Recursively add TRANSLATE: prefix to all string values."""
            for key, value in data.items():
                if isinstance(value, dict):
                    add_placeholders(value)
                elif isinstance(value, str):
                    data[key] = f"[TRANSLATE TO {lang_name.upper()}]: {value}"
            return data

        template = add_placeholders(template)

        with open(new_path, 'w', encoding='utf-8') as f:
            json.dump(template, f, ensure_ascii=False, indent=2)

        print(f"Created template for {lang_name} ({lang_code}) at {new_path}")
        print(f"Remember to:")
        print(f"1. Translate all strings marked with [TRANSLATE TO {lang_name.upper()}]")
        print(f"2. Remove the [TRANSLATE TO {lang_name.upper()}]: prefix after translation")
        print(f"3. Update config.py to include '{lang_code}' in supported_languages")
        print(f"4. Add language button to telegram_service.py handle_language method")

        return True


# Example: Adding German language support
def add_german_support():
    """Example of how to add German language support."""

    # Step 1: Create translation template
    validator = TranslationValidator()
    validator.create_language_template('de', 'German')

    # Step 2: Update config.py (manual step)
    print("\n📝 Update backend/app/core/config.py:")
    print("In validate_language method, change:")
    print("  supported_languages = ['en', 'ru']")
    print("To:")
    print("  supported_languages = ['en', 'ru', 'de']")

    # Step 3: Update telegram_service.py (manual step)
    print("\n📝 Update backend/app/services/telegram_service.py:")
    print("In handle_language method, add:")
    print('  InlineKeyboardButton("🇩🇪 Deutsch", callback_data="lang_de")')

    # Step 4: Example German translations (partial)
    german_translations = {
        "bot": {
            "welcome": "🤖 Willkommen bei {bot_name}!\n\n{description}\n\nBefehle:\n/help - Diese Hilfsnachricht anzeigen\n/new - Neue Unterhaltung starten\n/clear - Aktuelle Unterhaltung löschen\n/history - Letzte Unterhaltungen anzeigen\n/logout - Abmelden und erneut authentifizieren\n\nSenden Sie mir einfach eine Nachricht, um zu chatten!",
            "new_conversation": "✨ Neue Unterhaltung gestartet. Senden Sie mir Ihre Nachricht!",
            "conversation_cleared": "🧹 Gelöscht. Ihre nächste Nachricht startet eine neue Unterhaltung.",
            "nothing_to_clear": "Nichts zu löschen. Sie sind bereits bereit ✨",
            "no_history": "Keine Unterhaltungshistorie gefunden.",
            "logout_success": "✅ Sie wurden abgemeldet. Senden Sie Ihre E-Mail zur erneuten Authentifizierung."
        },
        "auth": {
            "required": "🔐 Bitte senden Sie Ihre E-Mail zur Authentifizierung{domains_hint}.",
            "success": "✅ Authentifizierung erfolgreich! Sie können jetzt chatten.",
            "invalid_code": "❌ Ungültiger oder abgelaufener Code. Bitte senden Sie Ihre E-Mail erneut."
        },
        "errors": {
            "dify_error": "❌ {message}",
            "generic_error": "Ein Fehler ist aufgetreten"
        }
    }

    # Save German translations
    de_path = validator.translations_dir / "de.json"
    with open(de_path, 'w', encoding='utf-8') as f:
        json.dump(german_translations, f, ensure_ascii=False, indent=2)

    print("\n✅ German language support template created!")
    print("Complete the translations in backend/app/core/translations/de.json")


# Validation script
def validate_all_languages():
    """Validate all language files against English reference."""
    validator = TranslationValidator()

    print("🔍 Validating all translation files...\n")

    for lang_file in validator.translations_dir.glob("*.json"):
        if lang_file.stem == "en":
            continue

        result = validator.validate_language_file(lang_file.stem)

        print(f"Language: {result.get('language', 'Unknown')}")
        print(f"Completion: {result.get('completion_percentage', 0)}%")
        print(f"Translated: {result.get('translated_keys', 0)}/{result.get('total_keys', 0)}")

        if result.get('missing_keys'):
            print(f"⚠️  Missing keys: {len(result['missing_keys'])}")
            for key in result['missing_keys'][:5]:  # Show first 5
                print(f"   - {key}")
            if len(result['missing_keys']) > 5:
                print(f"   ... and {len(result['missing_keys']) - 5} more")

        if result.get('extra_keys'):
            print(f"⚠️  Extra keys: {len(result['extra_keys'])}")
            for key in result['extra_keys'][:5]:
                print(f"   - {key}")

        print("-" * 50)


# CLI usage
if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage:")
        print("  python translation_helper.py validate     - Validate all translations")
        print("  python translation_helper.py add <code> <name> - Add new language")
        print("  python translation_helper.py check <code> - Check specific language")
        sys.exit(1)

    command = sys.argv[1]
    validator = TranslationValidator()

    if command == "validate":
        validate_all_languages()
    elif command == "add" and len(sys.argv) == 4:
        lang_code = sys.argv[2]
        lang_name = sys.argv[3]
        validator.create_language_template(lang_code, lang_name)
    elif command == "check" and len(sys.argv) == 3:
        lang_code = sys.argv[2]
        result = validator.validate_language_file(lang_code)
        print(json.dumps(result, indent=2))
    else:
        print("Invalid command")
