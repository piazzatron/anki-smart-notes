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

# Strip HTML is a generation setting like web search: the singleton defaults hold it,
# default-backed fields leave it NULL and inherit, customized fields store their own.
# Field HTML used to go into prompts as-is; every field starts stripping it now.
steps = [
    step(
        "ALTER TABLE default_text_generation_settings "
        "ADD COLUMN strip_html INTEGER NOT NULL DEFAULT 1 CHECK (strip_html IN (0, 1));",
        "SELECT 1;",
    ),
    step(
        "ALTER TABLE default_image_generation_settings "
        "ADD COLUMN strip_html INTEGER NOT NULL DEFAULT 1 CHECK (strip_html IN (0, 1));",
        "SELECT 1;",
    ),
    step(
        "ALTER TABLE text_smart_field_settings "
        "ADD COLUMN strip_html INTEGER CHECK (strip_html IN (0, 1));",
        "SELECT 1;",
    ),
    step(
        "ALTER TABLE image_smart_field_settings "
        "ADD COLUMN strip_html INTEGER CHECK (strip_html IN (0, 1));",
        "SELECT 1;",
    ),
    step(
        "UPDATE text_smart_field_settings SET strip_html = 1 "
        "WHERE uses_default_generation_settings = 0;",
        "SELECT 1;",
    ),
    step(
        "UPDATE image_smart_field_settings SET strip_html = 1 "
        "WHERE uses_default_generation_settings = 0;",
        "SELECT 1;",
    ),
]
