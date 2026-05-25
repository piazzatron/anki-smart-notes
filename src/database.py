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

from yoyo import read_migrations
from yoyo.backends.core.sqlite3 import SQLiteBackend
from yoyo.connections import default_migration_table, parse_uri

from .logger import logger

DATABASE_FILENAME = "smart_notes.sqlite3"
USER_FILES_DIR = "user_files"


def apply_database_migrations(
    database_path: Optional[str] = None,
    migration_count: Optional[int] = None,
) -> None:
    # Tests pass isolated temp DB paths so migration state never touches user data.
    resolved_database_path = database_path or get_database_path()
    Path(resolved_database_path).parent.mkdir(parents=True, exist_ok=True)

    logger.debug(f"Smart fields DB: preparing migrations for {resolved_database_path}")
    backend = get_sqlite_backend(resolved_database_path)
    migrations_path = Path(__file__).with_name("db_migrations")
    logger.debug(f"Smart fields DB: reading migrations from {migrations_path}")
    migrations = read_migrations(str(migrations_path))
    if migration_count is not None:
        migrations = migrations[:migration_count]

    with backend.lock():
        pending_migrations = backend.to_apply(migrations)
        if not pending_migrations:
            logger.debug("Smart fields DB: no pending migrations")
            return

        logger.info(
            f"Smart fields DB: applying {len(pending_migrations)} database migration(s)"
        )
        backend.apply_migrations(pending_migrations)
        logger.info("Smart fields DB: database migrations applied")


def open_database(database_path: Optional[str] = None) -> sqlite3.Connection:
    resolved_database_path = database_path or get_database_path()

    conn = sqlite3.connect(resolved_database_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def get_database_path() -> str:
    return get_user_files_path(DATABASE_FILENAME)


def get_user_files_path(filename: str) -> str:
    return str(Path(__file__).resolve().parent.parent / USER_FILES_DIR / filename)


def get_sqlite_backend(database_path: str) -> SQLiteBackend:
    # In Anki's vendored add-on environment, yoyo's package metadata may be missing.
    # Import the SQLite backend directly instead of relying on entry-point discovery.
    database_uri = f"sqlite:///{Path(database_path).absolute().as_posix()}"
    backend = SQLiteBackend(parse_uri(database_uri), default_migration_table)
    backend.init_database()
    return backend
