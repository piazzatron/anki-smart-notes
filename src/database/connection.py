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
from pathlib import Path
from typing import Optional

from yoyo.backends.core.sqlite3 import SQLiteBackend
from yoyo.connections import default_migration_table, parse_uri

DATABASE_FILENAME = "smart_notes.sqlite3"
USER_FILES_DIR = "user_files"


def open_database(database_path: Optional[str] = None) -> sqlite3.Connection:
    resolved_database_path = database_path or get_database_path()

    conn = sqlite3.connect(resolved_database_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def get_database_path() -> str:
    return get_user_files_path(DATABASE_FILENAME)


def get_user_files_path(filename: str) -> str:
    return str(Path(__file__).resolve().parents[2] / USER_FILES_DIR / filename)


def get_sqlite_backend(database_path: str) -> SQLiteBackend:
    # In Anki's vendored add-on environment, yoyo's package metadata may be missing.
    # Import the SQLite backend directly instead of relying on entry-point discovery.
    database_uri = f"sqlite:///{Path(database_path).absolute().as_posix()}"
    backend = SQLiteBackend(parse_uri(database_uri), default_migration_table)
    backend.init_database()
    return backend
