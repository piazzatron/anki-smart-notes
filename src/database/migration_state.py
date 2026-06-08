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

from sqlite3 import OperationalError
from typing import Optional

from . import connection

BOOTSTRAP_MIGRATION_ID = "0001_initial_smart_fields_schema"
PROFILE_SCOPE_MIGRATION_ID = "0003_scope_smart_fields_to_profile"
LEGACY_IMPORT_ALLOWED_PRE_IMPORT_MIGRATION_IDS = frozenset(
    {
        BOOTSTRAP_MIGRATION_ID,
        PROFILE_SCOPE_MIGRATION_ID,
    }
)


def applied_migration_ids(database_path: str) -> set[str]:
    with connection.open_database(database_path) as conn:
        try:
            rows = conn.execute("SELECT migration_id FROM _yoyo_migration").fetchall()
        except OperationalError:
            return set()

    return {str(row[0]) for row in rows}


def assert_legacy_config_import_can_run(
    database_path: Optional[str] = None,
) -> None:
    resolved_database_path = database_path or connection.get_database_path()
    applied_migrations = applied_migration_ids(resolved_database_path)
    if BOOTSTRAP_MIGRATION_ID not in applied_migrations:
        raise RuntimeError(
            "Cannot import legacy Smart Fields because the SQLite bootstrap "
            "migration has not run"
        )

    later_migrations = sorted(
        applied_migrations - LEGACY_IMPORT_ALLOWED_PRE_IMPORT_MIGRATION_IDS
    )
    if later_migrations:
        raise RuntimeError(
            "Cannot import legacy Smart Fields because SQL data migrations have "
            "already run before legacy config import: " + ", ".join(later_migrations)
        )
