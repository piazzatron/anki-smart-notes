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
from . import connection
from .legacy_config_migration import (
    legacy_config_migration_is_complete,
    migrate_legacy_config_to_database,
)

BOOTSTRAP_MIGRATION_ID = "0001_initial_smart_fields_schema"
PROFILE_SCOPE_MIGRATION_ID = "0003_scope_smart_fields_to_profile"


def run_migrations() -> None:
    # The upgrade pipeline intentionally has a narrow out-of-order repair:
    #
    # 1. Fresh installs run the edited bootstrap, import legacy config into that
    #    schema, then run every remaining SQL migration in order.
    # 2. Interrupted older installs may have yoyo's original bootstrap recorded
    #    without profile_name in the physical table. If legacy import is still
    #    pending, run only the profile-scope repair first so import can write
    #    valid rows; later data migrations still run after import.
    # 3. Installs that already imported legacy rows run the profile-scope
    #    compatibility migration in normal yoyo order, where it can map existing
    #    profile-local ids without guessing the currently-open profile.
    #
    # This keeps old config import at the earliest adequate schema while still
    # making later SQL migrations own each backfill exactly once.
    apply_database_bootstrap_migrations()
    apply_database_profile_scope_migration_if_needed()
    migrate_legacy_config_to_database()
    apply_database_migrations()


def apply_database_bootstrap_migrations(database_path: Optional[str] = None) -> None:
    _apply_migrations(
        database_path,
        selected_migration_ids={BOOTSTRAP_MIGRATION_ID},
    )


def apply_database_migrations(database_path: Optional[str] = None) -> None:
    _apply_migrations(database_path)


def apply_database_profile_scope_migration_if_needed(
    database_path: Optional[str] = None,
) -> None:
    resolved_database_path = database_path or connection.get_database_path()
    if not _database_has_unprofiled_smart_fields_schema(resolved_database_path):
        return

    if legacy_config_migration_is_complete():
        return

    logger.info(
        "Smart fields DB: applying profile-scope compatibility migration before "
        "legacy config import"
    )
    _apply_migrations(
        database_path,
        selected_migration_ids={PROFILE_SCOPE_MIGRATION_ID},
    )


def _apply_migrations(
    database_path: Optional[str] = None,
    selected_migration_ids: Optional[set[str]] = None,
) -> None:
    # Tests pass isolated temp DB paths so migration state never touches user data.
    resolved_database_path = database_path or connection.get_database_path()
    Path(resolved_database_path).parent.mkdir(parents=True, exist_ok=True)

    logger.debug(f"Smart fields DB: preparing migrations for {resolved_database_path}")
    backend = connection.get_sqlite_backend(resolved_database_path)
    migrations_path = Path(__file__).with_name("db_migrations")
    logger.debug(f"Smart fields DB: reading migrations from {migrations_path}")
    migrations = read_migrations(str(migrations_path))
    if selected_migration_ids is not None:
        migrations = migrations.filter(
            lambda migration: migration.id in selected_migration_ids
        )

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
