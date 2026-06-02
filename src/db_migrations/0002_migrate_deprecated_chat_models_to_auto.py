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

steps = [
    step(
        """
        UPDATE default_text_generation_settings
        SET provider = 'auto', model = 'auto'
        WHERE model IN ('deepseek-v3', 'gpt-4o-mini', 'gpt-5-nano');
        """,
        "SELECT 1;",
    ),
    step(
        """
        UPDATE text_smart_field_settings
        SET provider = 'auto', model = 'auto'
        WHERE uses_default_generation_settings = 0
            AND model IN ('deepseek-v3', 'gpt-4o-mini', 'gpt-5-nano');
        """,
        "SELECT 1;",
    ),
]
