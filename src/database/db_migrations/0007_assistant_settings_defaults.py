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
    # `model` and `reasoning_level` are deliberately unCHECKed: the catalog can
    # change without requiring a database migration.
    step(
        "ALTER TABLE assistant_settings ADD COLUMN model TEXT NOT NULL DEFAULT 'auto';",
        "ALTER TABLE assistant_settings DROP COLUMN model;",
    ),
    step(
        "ALTER TABLE assistant_settings ADD COLUMN reasoning_level TEXT NOT NULL DEFAULT 'off';",
        "ALTER TABLE assistant_settings DROP COLUMN reasoning_level;",
    ),
    step(
        "ALTER TABLE assistant_settings ADD COLUMN show_reasoning INTEGER NOT NULL DEFAULT 0;",
        "ALTER TABLE assistant_settings DROP COLUMN show_reasoning;",
    ),
    step(
        "ALTER TABLE assistant_settings ADD COLUMN show_credit_usage INTEGER NOT NULL DEFAULT 0;",
        "ALTER TABLE assistant_settings DROP COLUMN show_credit_usage;",
    ),
]
