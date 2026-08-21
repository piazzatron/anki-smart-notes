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
        CREATE TABLE assistant_prompts (
            id TEXT PRIMARY KEY,
            profile_name TEXT NOT NULL,
            label TEXT NOT NULL,
            prompt_text TEXT NOT NULL,
            position INTEGER NOT NULL
        );
        """,
        "DROP TABLE assistant_prompts;",
    ),
    # A profile is seeded with the starter prompt exactly once. Without this
    # marker, deleting every prompt would look identical to a new profile and
    # the starter would come back on the next read.
    step(
        """
        CREATE TABLE assistant_prompt_seeds (
            profile_name TEXT PRIMARY KEY
        );
        """,
        "DROP TABLE assistant_prompt_seeds;",
    ),
]
