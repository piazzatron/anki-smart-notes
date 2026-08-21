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
    # One row per profile, absent until something is changed: for settings, no
    # row simply means every default. `response_language` holds a language code
    # ('auto' for "match what the user writes") and is deliberately unCHECKed —
    # the supported list grows, and a CHECK would mean a migration each time.
    step(
        """
        CREATE TABLE assistant_settings (
            profile_name TEXT PRIMARY KEY,
            response_language TEXT NOT NULL DEFAULT 'auto'
        );
        """,
        "DROP TABLE assistant_settings;",
    ),
]
