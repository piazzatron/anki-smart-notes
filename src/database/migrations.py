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

# How Smart Fields migrations work (and why they're weird)
# =========================================================
#
# This comment is the canonical story for Smart Fields migrations; the specs in
# the top-level repo point here. specs/migration-design.md covers the general
# upgrade-pipeline philosophy.
#
# There are two unusual things about this migration setup:
#
# 1. The run order interleaves SQL and Python. run_migrations() applies the
#    bootstrap migration (0001, schema only), then runs the legacy config.json
#    import (Python — it needs mw and the Anki collection to resolve note type
#    names to ids, so it can't be a yoyo migration), then applies the remaining
#    SQL data migrations (0002+). Data migrations must run AFTER the import so
#    that imported rows get backfilled too: a user who jumps several versions at
#    once gets their config imported first, then every backfill in order. The idea
#    is that model migrations etc (chatgpt 4 -> 5 -> 6)
#    in a single place (the SQL); get users into a clean state, move their data over,
#    then let the SQL do the rest.
#
# 2. Migration 0001 was rewritten after it shipped. The v2.22.x bootstrap
#    created smart_fields WITHOUT profile_name; v2.23.0 edited 0001 in place
#    to include it. Editing an applied migration is normally forbidden — this
#    is the bug that forced it:
#
#    The legacy prompts_map was keyed by note type NAME. Names are portable
#    across Anki profiles, but note type ids are NOT: the same note type name
#    resolves to a DIFFERENT id in every profile (deck ids are profile-local
#    too). So a name-keyed smart field "existed" in whichever profile had a
#    note type with that name. The v2.22.x import collapsed the name-keyed
#    data into ids resolved against ONLY the currently open profile — names
#    missing from that profile were silently dropped, and even names that
#    existed in several profiles got pinned to the open profile's ids, so
#    every OTHER profile lost its smart fields. And because the import deletes
#    the legacy config keys on success, the user was at that point fully
#    migrated to SQL — unrecoverable beyond the config backup saved to
#    user_files. That was the nasty bug.
#
#    The fix: make the schema profile-scoped from the FIRST migration, so the
#    Python legacy import can be profile-aware — it fans each name-keyed entry
#    out to every profile whose collection has that note type name (skipping
#    deck ids that don't exist in that profile) and stamps profile_name on
#    each row it writes.
#
#    - Fresh installs and not-yet-imported upgraders: 0001 creates the
#      profile-scoped schema, the import fans out as above, and 0003 sees
#      profile_name already present and no-ops.
#    - Users who already ran the 2.22.x import: yoyo recorded 0001 as applied
#      with the OLD schema, and their rows are bare (note_type_id, deck_id)
#      pairs — the names are long gone, so the fan-out can't be replayed. 0003
#      rebuilds their table best-effort from that lossy data: it scans every
#      readable profile and keeps only rows whose ids it can place confidently
#      (cloning rows that match multiple profiles, dropping rows no profile
#      can claim).
#
#    The upshot: "0001 applied" means different schemas on different machines,
#    and 0003 is the compatibility shim that converges them.
#
# The partial-upgrade recovery below exists because of fork #2: a 2.22.x user
# whose legacy import crashed (the completion flag is only set after a fully
# successful import) still has the old unprofiled table recorded as bootstrapped.
# For them the import would run before 0003 adds profile_name and crash
# mid-write. Their data is safe because legacy config keys are only removed as
# the import's final step, so we back up the stale partial DB, recreate the
# profile-aware bootstrap, and run the normal legacy import.

from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from yoyo import read_migrations

from ..config import config
from ..logger import logger
from ..telemetry import track_event
from . import connection
from .legacy_config_migration import migrate_legacy_config_to_database


def run_migrations() -> None:
    apply_database_bootstrap_migrations()
    _recover_legacy_import_pending_unprofiled_schema()
    migrate_legacy_config_to_database()
    apply_database_migrations()


def _recover_legacy_import_pending_unprofiled_schema() -> None:
    # Detects the partial 2.22.x upgrade described at the top of this file:
    # import pending but the table predates profile_name. Legacy config remains
    # authoritative until the import succeeds, so a stale partial DB can be
    # backed up and recreated before the profile-aware import runs.
    if config.did_migrate_smart_fields_to_sqlite:
        return

    database_path = Path(connection.get_database_path())
    if not database_path.exists():
        return

    with connection.open_database(str(database_path)) as conn:
        has_smart_fields = (
            conn.execute(
                "SELECT 1 FROM sqlite_master "
                "WHERE type = 'table' AND name = 'smart_fields'"
            ).fetchone()
            is not None
        )
        if not has_smart_fields:
            return

        columns = {row[1] for row in conn.execute("PRAGMA table_info(smart_fields)")}
        if "profile_name" in columns:
            return

    backup_path = _partial_upgrade_backup_path(database_path)
    logger.info(
        "Smart fields DB: recovering legacy-import-pending unprofiled schema "
        f"by backing up {database_path} to {backup_path}"
    )
    database_path.replace(backup_path)
    apply_database_bootstrap_migrations(str(database_path))
    logger.info("Smart fields DB: recreated profiled bootstrap after partial upgrade")
    track_event("smart_fields_partial_migration_recovered")


def apply_database_bootstrap_migrations(database_path: Optional[str] = None) -> None:
    _apply_migrations(database_path, bootstrap_only=True)


def apply_database_migrations(database_path: Optional[str] = None) -> None:
    _apply_migrations(database_path)


def _apply_migrations(
    database_path: Optional[str] = None,
    bootstrap_only: bool = False,
) -> None:
    # Tests pass isolated temp DB paths so migration state never touches user data.
    resolved_database_path = database_path or connection.get_database_path()
    Path(resolved_database_path).parent.mkdir(parents=True, exist_ok=True)

    logger.info(f"Smart fields DB: preparing migrations for {resolved_database_path}")
    with connection.get_sqlite_backend(resolved_database_path) as backend:
        migrations_path = Path(__file__).with_name("db_migrations")
        logger.info(f"Smart fields DB: reading migrations from {migrations_path}")
        migrations = read_migrations(str(migrations_path))
        if bootstrap_only:
            migrations = migrations[:1]

        with backend.lock():
            pending_migrations = backend.to_apply(migrations)
            if not pending_migrations:
                logger.info("Smart fields DB: no pending migrations")
                return

            logger.info(
                f"Smart fields DB: applying {len(pending_migrations)} database migration(s)"
            )
            backend.apply_migrations(pending_migrations)
            logger.info("Smart fields DB: database migrations applied")


def _partial_upgrade_backup_path(database_path: Path) -> Path:
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    # Keep this backup for support diagnostics instead of treating it as a temp file.
    return database_path.with_name(
        f"{database_path.name}.partial-upgrade-backup-{timestamp}"
    )
