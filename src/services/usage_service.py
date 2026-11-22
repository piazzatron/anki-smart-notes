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

import sqlite3

from .. import utils
from ..config import config
from ..database.connection import open_database


def _ensure_row(conn: sqlite3.Connection, profile_name: str) -> None:
    # A profile's first read carries over the count the config file kept for the
    # whole install before the count moved here.
    conn.execute(
        "INSERT OR IGNORE INTO usage_counts (profile_name, times_used) VALUES (?, ?)",
        (profile_name, config.times_used or 0),
    )


def get_times_used() -> int:
    """How many generations the user has started in this profile."""
    profile_name = utils.get_current_profile_name()
    with open_database() as conn:
        _ensure_row(conn, profile_name)
        row = conn.execute(
            "SELECT times_used FROM usage_counts WHERE profile_name = ?",
            (profile_name,),
        ).fetchone()
    return int(row["times_used"])


def bump_times_used() -> int:
    """Counts one generation in this profile and returns the new count."""
    profile_name = utils.get_current_profile_name()
    with open_database() as conn:
        _ensure_row(conn, profile_name)
        # One transaction: SQLite holds the write lock from the UPDATE to the commit.
        conn.execute(
            "UPDATE usage_counts SET times_used = times_used + 1 WHERE profile_name = ?",
            (profile_name,),
        )
        row = conn.execute(
            "SELECT times_used FROM usage_counts WHERE profile_name = ?",
            (profile_name,),
        ).fetchone()
    return int(row["times_used"])


def set_times_used(count: int) -> None:
    """Sets this profile's count, for dev tooling."""
    profile_name = utils.get_current_profile_name()
    with open_database() as conn:
        conn.execute(
            "INSERT INTO usage_counts (profile_name, times_used) VALUES (?, ?) "
            "ON CONFLICT (profile_name) DO UPDATE SET times_used = excluded.times_used",
            (profile_name, count),
        )
