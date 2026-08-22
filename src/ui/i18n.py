"""
Copyright (C) 2024 Michael Piazza

This file is part of Smart Notes.

Smart Notes is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

Smart Notes is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with Smart Notes.  If not, see <https://www.gnu.org/licenses/>.
"""

from typing import Literal

from anki import lang

from .native_action_translations import NATIVE_ACTION_TRANSLATIONS

NativeActionKey = Literal[
    "open_smart_notes",
    "generate_smart_fields",
    "generate_smart_field",
    "custom_text",
    "custom_tts",
    "custom_image",
]

_LOCALE_BY_LOWERCASE = {locale.lower(): locale for locale in NATIVE_ACTION_TRANSLATIONS}


def native_action_text(key: NativeActionKey) -> str:
    """Return native Anki action copy in Anki's interface language."""
    locale = _match_native_action_locale(lang.current_lang)
    return NATIVE_ACTION_TRANSLATIONS[locale][key]


def _match_native_action_locale(requested_locale: str) -> str:
    normalized = requested_locale.replace("_", "-").lower()
    exact = _LOCALE_BY_LOWERCASE.get(normalized)
    if exact is not None:
        return exact

    primary = normalized.split("-", maxsplit=1)[0]
    return _LOCALE_BY_LOWERCASE.get(primary, "en")
