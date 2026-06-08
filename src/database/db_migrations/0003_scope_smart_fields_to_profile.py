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

import logging
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from uuid import uuid4

from anki.collection import Collection
from aqt import mw
from yoyo import step

GLOBAL_DECK_ID = -1
SETTING_TABLES = (
    "text_smart_field_settings",
    "tts_smart_field_settings",
    "image_smart_field_settings",
)

logger = logging.getLogger("smart_notes")


@dataclass(frozen=True)
class _ProfileContext:
    profile_name: str
    note_type_ids: set[int]
    deck_ids: set[int]


@dataclass(frozen=True)
class _ScopedSmartField:
    old_id: str
    new_id: str
    profile_name: str
    row: dict[str, object]


def _scope_smart_fields_to_profile(conn: sqlite3.Connection) -> None:
    columns = _smart_field_columns(conn)
    if "profile_name" in columns:
        return

    # Fresh bootstrap databases are already profile-scoped. This compatibility
    # migration is only for databases that ran the old bootstrap and legacy import
    # before `profile_name` existed, after the original prompt-map names may have
    # been removed from config.json. At that point the surviving rows contain only
    # profile-local note type/deck ids. Stamping every row with the currently open
    # profile would silently move fields when the user later opens a different
    # profile, so this migration scans each readable profile collection and only
    # keeps rows whose existing ids can be placed confidently.
    old_rows = _rows_as_dicts(
        conn,
        """
        SELECT
            id, note_type_id, deck_id, target_field_name, field_type,
            enabled, created_at, updated_at
        FROM smart_fields
        ORDER BY id
        """,
    )
    settings_by_table = _setting_rows_by_table(conn)
    scoped_rows: list[_ScopedSmartField] = []
    if old_rows:
        scoped_rows = _scoped_smart_field_rows(old_rows, _get_profile_contexts())

    _create_profile_scoped_smart_fields_table(conn)
    for scoped_row in scoped_rows:
        _insert_profile_scoped_smart_field(conn, scoped_row)

    for table in SETTING_TABLES:
        if _table_exists(conn, table):
            conn.execute(f"DELETE FROM {table}")

    conn.execute("DROP TABLE smart_fields;")
    conn.execute("ALTER TABLE smart_fields_new RENAME TO smart_fields;")
    _insert_scoped_setting_rows(conn, scoped_rows, settings_by_table)


def _undo_scope_smart_fields_to_profile(conn: sqlite3.Connection) -> None:
    raise RuntimeError(
        "Cannot roll back Smart Fields profile scoping safely: rows and settings "
        "may have been cloned into multiple profiles, and choosing one profile "
        "would silently discard data."
    )


def _smart_field_columns(conn: sqlite3.Connection) -> set[str]:
    return {row[1] for row in conn.execute("PRAGMA table_info(smart_fields)")}


def _rows_as_dicts(
    conn: sqlite3.Connection, query: str, params: tuple[object, ...] = ()
) -> list[dict[str, object]]:
    cursor = conn.execute(query, params)
    columns = [description[0] for description in cursor.description]
    return [dict(zip(columns, row)) for row in cursor.fetchall()]


def _setting_rows_by_table(
    conn: sqlite3.Connection,
) -> dict[str, dict[str, dict[str, object]]]:
    settings_by_table: dict[str, dict[str, dict[str, object]]] = {}
    for table in SETTING_TABLES:
        if not _table_exists(conn, table):
            settings_by_table[table] = {}
            continue

        settings_by_table[table] = {
            str(row["smart_field_id"]): row
            for row in _rows_as_dicts(conn, f"SELECT * FROM {table}")
        }
    return settings_by_table


def _table_exists(conn: sqlite3.Connection, table: str) -> bool:
    return (
        conn.execute(
            "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = ?",
            (table,),
        ).fetchone()
        is not None
    )


def _scoped_smart_field_rows(
    old_rows: list[dict[str, object]], profile_contexts: list[_ProfileContext]
) -> list[_ScopedSmartField]:
    scoped_rows: list[_ScopedSmartField] = []
    for old_row in old_rows:
        old_id = str(old_row["id"])
        matching_contexts = _matching_profile_contexts(old_row, profile_contexts)
        if not matching_contexts:
            logger.warning(
                "Smart Fields profile migration: skipping unprofiled smart field "
                f"id={old_id}, note_type_id={old_row['note_type_id']}, "
                f"deck_id={old_row['deck_id']}, "
                f"target_field={old_row['target_field_name']} because no readable "
                "profile has those ids"
            )
            continue

        for index, context in enumerate(matching_contexts):
            scoped_rows.append(
                _ScopedSmartField(
                    old_id=old_id,
                    new_id=old_id if index == 0 else str(uuid4()),
                    profile_name=context.profile_name,
                    row=old_row,
                )
            )

    return scoped_rows


def _matching_profile_contexts(
    old_row: dict[str, object], profile_contexts: list[_ProfileContext]
) -> list[_ProfileContext]:
    note_type_id = _int_value(old_row["note_type_id"])
    deck_id = _int_value(old_row["deck_id"])
    return [
        context
        for context in profile_contexts
        if note_type_id in context.note_type_ids
        and (deck_id == GLOBAL_DECK_ID or deck_id in context.deck_ids)
    ]


def _get_profile_contexts() -> list[_ProfileContext]:
    # This intentionally duplicates the low-level profile scan used by the
    # prompt-map importer. Yoyo loads migration files as standalone scripts by
    # path, and this file must remain stable for old databases even as runtime
    # services and importers evolve. Coupling it to SmartFieldService or the
    # legacy importer would make a compatibility migration depend on unrelated
    # runtime invariants.
    if not mw or not mw.pm or not mw.col:
        raise RuntimeError(
            "Cannot scope Smart Fields because Anki profiles are unavailable"
        )

    current_profile = _current_profile_name_for_profile_migration()
    profile_names = [str(profile_name) for profile_name in mw.pm.profiles()]
    if current_profile not in profile_names:
        profile_names.append(current_profile)

    # Opening other profile collections can trigger Anki collection-level
    # housekeeping, but old unprofiled rows only have profile-local ids. Scanning
    # each profile is the only way to avoid pinning them to the current profile.
    contexts: list[_ProfileContext] = []
    for profile_name in profile_names:
        collection = mw.col
        close_after = False
        if profile_name != current_profile:
            collection_path = Path(str(mw.pm.base)) / profile_name / "collection.anki2"
            if not collection_path.exists():
                logger.warning(
                    "Smart Fields profile migration: skipping profile="
                    f"{profile_name} because collection.anki2 does not exist"
                )
                continue

            try:
                collection = Collection(str(collection_path))
            except Exception:
                logger.warning(
                    "Smart Fields profile migration: skipping profile="
                    f"{profile_name} because collection.anki2 could not be opened",
                    exc_info=True,
                )
                continue
            close_after = True

        try:
            contexts.append(_profile_context(profile_name, collection))
        except Exception:
            if profile_name == current_profile:
                raise
            logger.warning(
                "Smart Fields profile migration: skipping profile="
                f"{profile_name} because collection metadata could not be read",
                exc_info=True,
            )
        finally:
            if close_after:
                collection.close()

    return contexts


def _current_profile_name_for_profile_migration() -> str:
    if not mw or not mw.pm or not mw.pm.name:
        raise RuntimeError(
            "Cannot scope Smart Fields because Anki profile is unavailable"
        )
    return str(mw.pm.name)


def _profile_context(profile_name: str, collection: Any) -> _ProfileContext:
    return _ProfileContext(
        profile_name=profile_name,
        note_type_ids={int(model["id"]) for model in collection.models.all()},
        deck_ids={int(deck["id"]) for deck in collection.decks.all()},
    )


def _create_profile_scoped_smart_fields_table(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE smart_fields_new (
            id TEXT PRIMARY KEY,
            profile_name TEXT NOT NULL,
            note_type_id INTEGER NOT NULL,
            deck_id INTEGER NOT NULL,
            target_field_name TEXT NOT NULL,
            field_type TEXT NOT NULL CHECK (field_type IN ('chat', 'tts', 'image')),
            enabled INTEGER NOT NULL DEFAULT 1 CHECK (enabled IN (0, 1)),
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            UNIQUE(profile_name, note_type_id, deck_id, target_field_name)
        );
        """
    )


def _insert_profile_scoped_smart_field(
    conn: sqlite3.Connection, scoped_row: _ScopedSmartField
) -> None:
    row = scoped_row.row
    conn.execute(
        """
        INSERT INTO smart_fields_new (
            id, profile_name, note_type_id, deck_id, target_field_name, field_type,
            enabled, created_at, updated_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            scoped_row.new_id,
            scoped_row.profile_name,
            _int_value(row["note_type_id"]),
            _int_value(row["deck_id"]),
            str(row["target_field_name"]),
            str(row["field_type"]),
            _int_value(row["enabled"]),
            str(row["created_at"]),
            str(row["updated_at"]),
        ),
    )


def _insert_scoped_setting_rows(
    conn: sqlite3.Connection,
    scoped_rows: list[_ScopedSmartField],
    settings_by_table: dict[str, dict[str, dict[str, object]]],
) -> None:
    for table in SETTING_TABLES:
        if not _table_exists(conn, table):
            continue

        old_settings_by_id = settings_by_table[table]
        for scoped_row in scoped_rows:
            if scoped_row.old_id not in old_settings_by_id:
                continue

            setting_row = dict(old_settings_by_id[scoped_row.old_id])
            setting_row["smart_field_id"] = scoped_row.new_id

            # Preserve every setting column exactly as it existed in this old
            # schema. Later ordered migrations own any column-specific backfills.
            columns = list(setting_row)
            placeholders = ", ".join("?" for _ in columns)
            conn.execute(
                f"""
                INSERT INTO {table} ({", ".join(columns)})
                VALUES ({placeholders})
                """,
                tuple(setting_row[column] for column in columns),
            )


def _int_value(value: object) -> int:
    if isinstance(value, int):
        return int(value)
    if isinstance(value, str):
        return int(value)
    raise TypeError(f"Expected integer-compatible SQLite value, got {type(value)}")


steps = [
    step(_scope_smart_fields_to_profile, _undo_scope_smart_fields_to_profile),
]
