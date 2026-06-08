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

from pathlib import Path
from typing import Optional

from yoyo import read_migrations

from ..logger import logger
from ..ui.ui_utils import show_message_box
from . import connection
from .legacy_config_migration import (
    legacy_config_migration_is_complete,
    migrate_legacy_config_to_database,
)


def run_migrations() -> None:
    # Bootstrap creates the schema only. Generation defaults and Smart Fields
    # both come from legacy config.json, so import both before SQL data
    # migrations. That keeps future model backfills simple: update the default
    # row plus custom override rows, and inherited fields follow automatically.
    apply_database_bootstrap_migrations()
    _fail_if_legacy_import_would_use_unprofiled_schema()
    migrate_legacy_config_to_database()
    apply_database_migrations()


def apply_database_bootstrap_migrations(database_path: Optional[str] = None) -> None:
    _apply_migrations(database_path, bootstrap_only=True)


def apply_database_migrations(database_path: Optional[str] = None) -> None:
    _apply_migrations(database_path)


def _fail_if_legacy_import_would_use_unprofiled_schema(
    database_path: Optional[str] = None,
) -> None:
    if legacy_config_migration_is_complete():
        return

    resolved_database_path = database_path or connection.get_database_path()
    if not _database_has_unprofiled_smart_fields_schema(resolved_database_path):
        return

    # This should never happen in the supported runner: bootstrap and legacy
    # import are treated as one upgrade unit. If the user is here, support needs
    # to inspect and repair the partial upgrade state instead of continuing.
    show_message_box(
        "Smart Notes could not finish upgrading your Smart Fields.",
        "Please email support@smart-notes.xyz and include your smart-notes.log file.",
    )
    raise RuntimeError(
        "Smart Fields SQLite migration is in an unsupported partial upgrade state: "
        "legacy config import is pending, but smart_fields lacks profile_name"
    )


def _apply_migrations(
    database_path: Optional[str] = None,
    bootstrap_only: bool = False,
) -> None:
    # Tests pass isolated temp DB paths so migration state never touches user data.
    resolved_database_path = database_path or connection.get_database_path()
    Path(resolved_database_path).parent.mkdir(parents=True, exist_ok=True)

    logger.debug(f"Smart fields DB: preparing migrations for {resolved_database_path}")
    backend = connection.get_sqlite_backend(resolved_database_path)
    migrations_path = Path(__file__).with_name("db_migrations")
    logger.debug(f"Smart fields DB: reading migrations from {migrations_path}")
    migrations = read_migrations(str(migrations_path))
    if bootstrap_only:
        migrations = migrations[:1]

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


def _database_has_unprofiled_smart_fields_schema(database_path: str) -> bool:
    if not Path(database_path).exists():
        return False

    with connection.open_database(database_path) as conn:
        has_smart_fields = (
            conn.execute(
                "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = 'smart_fields'"
            ).fetchone()
            is not None
        )
        if not has_smart_fields:
            return False

        columns = {row[1] for row in conn.execute("PRAGMA table_info(smart_fields)")}

    return "profile_name" not in columns
