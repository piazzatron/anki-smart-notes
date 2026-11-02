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

from yoyo import step

# Older plugins saved names the server remaps to newer models. Settings move to the
# real names of the models those names already run.
TEXT_MODEL_RENAMES = {
    "gpt-5-mini": "gpt-6-luna",
    "gpt-5-chat-latest": "gpt-6.1-terra",
    "gpt-5": "gpt-6.1-sol",
    "claude-haiku-4-5": "claude-haiku-5-5",
    "claude-sonnet-4-6": "claude-sonnet-5-5",
    "claude-opus-4-6": "claude-opus-5-5",
    "gemini-3.1-flash-lite": "gemini-3.5-flash-lite",
    "gemini-3-flash": "gemini-3.8-flash",
    "gemini-3.1-pro": "gemini-4-argon",
}
IMAGE_MODEL_RENAMES = {"nano-banana-2": "nano-banana-2.1"}


def _rename(renames: dict[str, str]) -> str:
    cases = " ".join(f"WHEN '{old}' THEN '{new}'" for old, new in renames.items())
    return f"model = CASE model {cases} ELSE model END"


steps = [
    step(
        f"UPDATE default_text_generation_settings SET {_rename(TEXT_MODEL_RENAMES)};",
        "SELECT 1;",
    ),
    step(
        f"UPDATE text_smart_field_settings SET {_rename(TEXT_MODEL_RENAMES)};",
        "SELECT 1;",
    ),
    step(
        f"UPDATE default_image_generation_settings SET {_rename(IMAGE_MODEL_RENAMES)};",
        "SELECT 1;",
    ),
    step(
        f"UPDATE image_smart_field_settings SET {_rename(IMAGE_MODEL_RENAMES)};",
        "SELECT 1;",
    ),
]
