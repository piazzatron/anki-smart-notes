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
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import Any

import pytest
import yoyo.backends.base
from yoyo import read_migrations

import src.database.migrations as migrations_module
from src.database import (
    get_database_path,
    get_sqlite_backend,
    open_database,
)
from src.database.migrations import apply_database_migrations
from tests.fake_anki_profiles import install_fake_profile_collections, profile_data


def test_apply_database_migrations_creates_smart_field_tables(tmp_path: Path) -> None:
    database_path = tmp_path / "smart_notes.sqlite3"

    apply_database_migrations(str(database_path))

    conn = sqlite3.connect(database_path)
    try:
        tables = {
            row[0]
            for row in conn.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table'"
            ).fetchall()
        }

        assert "smart_fields" in tables
        assert "text_smart_field_settings" in tables
        assert "tts_smart_field_settings" in tables
        assert "image_smart_field_settings" in tables
        assert "default_text_generation_settings" in tables
        assert "default_tts_generation_settings" in tables
        assert "default_image_generation_settings" in tables

        smart_field_columns = {
            row[1] for row in conn.execute("PRAGMA table_info(smart_fields)")
        }
        assert smart_field_columns == {
            "id",
            "profile_name",
            "note_type_id",
            "deck_id",
            "target_field_name",
            "field_type",
            "enabled",
            "created_at",
            "updated_at",
        }
    finally:
        conn.close()


def test_apply_database_migrations_does_not_require_yoyo_entry_points(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setattr(yoyo.backends.base, "entry_points", lambda group: {})

    apply_database_migrations(str(tmp_path / "smart_notes.sqlite3"))


def test_apply_database_migrations_closes_backend_when_no_migrations(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    calls: list[str] = []

    class FakeBackend:
        def __enter__(self) -> "FakeBackend":
            calls.append("enter")
            return self

        def __exit__(self, *_: Any) -> None:
            calls.append("exit")

        @contextmanager
        def lock(self) -> Iterator[None]:
            calls.append("lock")
            yield

        def to_apply(self, _: object) -> list[object]:
            calls.append("to_apply")
            return []

    monkeypatch.setattr(
        migrations_module.connection,
        "get_sqlite_backend",
        lambda _: FakeBackend(),
    )
    monkeypatch.setattr(migrations_module, "read_migrations", lambda _: [])

    apply_database_migrations(str(tmp_path / "smart_notes.sqlite3"))

    assert calls == ["enter", "lock", "to_apply", "exit"]


def test_open_database_closes_connection_after_context(tmp_path: Path) -> None:
    database_path = tmp_path / "smart_notes.sqlite3"

    with open_database(str(database_path)) as conn:
        conn.execute("CREATE TABLE example(id INTEGER PRIMARY KEY)")

    with pytest.raises(sqlite3.ProgrammingError, match="closed database"):
        conn.execute("SELECT 1")


def test_deprecated_chat_models_migrate_to_auto(tmp_path: Path) -> None:
    database_path = tmp_path / "smart_notes.sqlite3"
    migrations_path = Path(__file__).parents[1] / "src" / "database" / "db_migrations"
    migrations = read_migrations(str(migrations_path))
    backend = get_sqlite_backend(str(database_path))

    with backend.lock():
        backend.apply_migrations(migrations[:1])

    conn = sqlite3.connect(database_path)
    try:
        for index, model in enumerate(
            ["deepseek-v3", "gpt-4o-mini", "gpt-5-nano", "gpt-5-mini"]
        ):
            smart_field_id = f"field-{index}"
            conn.execute(
                """
                INSERT INTO smart_fields (
                    id, profile_name, note_type_id, deck_id, target_field_name, field_type,
                    enabled, created_at, updated_at
                )
                VALUES (?, '__test__', 1, 1, ?, 'chat', 1, 'now', 'now')
                """,
                (smart_field_id, f"Field {index}"),
            )
            conn.execute(
                """
                INSERT INTO text_smart_field_settings (
                    smart_field_id, prompt_text, uses_default_generation_settings,
                    provider, model, reasoning_level, web_search_enabled
                )
                VALUES (?, 'prompt', 0, ?, ?, 'off', 0)
                """,
                (
                    smart_field_id,
                    "deepseek" if model == "deepseek-v3" else "openai",
                    model,
                ),
            )
        conn.commit()
    finally:
        conn.close()

    with backend.lock():
        backend.apply_migrations(migrations[1:])

    conn = sqlite3.connect(database_path)
    try:
        rows = conn.execute(
            """
            SELECT smart_field_id, provider, model
            FROM text_smart_field_settings
            ORDER BY smart_field_id
            """
        ).fetchall()
    finally:
        conn.close()

    assert rows == [
        ("field-0", "auto", "auto"),
        ("field-1", "auto", "auto"),
        ("field-2", "auto", "auto"),
        ("field-3", "openai", "gpt-5-mini"),
    ]


def test_deprecated_default_chat_model_migrates_to_auto(tmp_path: Path) -> None:
    database_path = tmp_path / "smart_notes.sqlite3"
    migrations_path = Path(__file__).parents[1] / "src" / "database" / "db_migrations"
    migrations = read_migrations(str(migrations_path))
    backend = get_sqlite_backend(str(database_path))

    with backend.lock():
        backend.apply_migrations(migrations[:1])

    conn = sqlite3.connect(database_path)
    try:
        conn.execute(
            """
            UPDATE default_text_generation_settings
            SET provider = 'openai', model = 'gpt-5-nano'
            WHERE id = 1
            """
        )
        conn.commit()
    finally:
        conn.close()

    with backend.lock():
        backend.apply_migrations(migrations[1:])

    conn = sqlite3.connect(database_path)
    try:
        row = conn.execute(
            """
            SELECT provider, model
            FROM default_text_generation_settings
            WHERE id = 1
            """
        ).fetchone()
    finally:
        conn.close()

    assert row == ("auto", "auto")


def test_profile_scope_migration_allows_same_field_in_different_profiles(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    database_path = tmp_path / "smart_notes.sqlite3"
    install_fake_migration_profiles(
        monkeypatch,
        tmp_path,
        profiles={"__test__": ({1}, {1})},
    )

    conn = sqlite3.connect(database_path)
    try:
        create_old_unprofiled_smart_field_schema(conn)
        insert_old_text_smart_field(conn, "legacy", 1, 1, "Back", "{{Front}}")
        conn.commit()

        conn.close()

        apply_profile_scope_migration(database_path)

        conn = sqlite3.connect(database_path)
        joined_row = conn.execute(
            """
            SELECT sf.profile_name, text.prompt_text, text.provider, text.model
            FROM smart_fields sf
            JOIN text_smart_field_settings text ON text.smart_field_id = sf.id
            WHERE sf.id = 'legacy'
            """
        ).fetchone()

        assert joined_row == ("__test__", "{{Front}}", "openai", "gpt-5-mini")

        conn.execute(
            """
            INSERT INTO smart_fields (
                id, profile_name, note_type_id, deck_id, target_field_name,
                field_type, enabled, created_at, updated_at
            )
            VALUES ('profile-1', 'Profile 1', 1, 1, 'Back', 'chat', 1, 'now', 'now')
            """
        )
        conn.execute(
            """
            INSERT INTO smart_fields (
                id, profile_name, note_type_id, deck_id, target_field_name,
                field_type, enabled, created_at, updated_at
            )
            VALUES ('profile-2', 'Profile 2', 1, 1, 'Back', 'chat', 1, 'now', 'now')
            """
        )

        with pytest.raises(sqlite3.IntegrityError):
            conn.execute(
                """
                INSERT INTO smart_fields (
                    id, profile_name, note_type_id, deck_id, target_field_name,
                    field_type, enabled, created_at, updated_at
                )
                VALUES (
                    'profile-1-duplicate', 'Profile 1', 1, 1, 'Back',
                    'chat', 1, 'now', 'now'
                )
                """
            )
    finally:
        conn.close()


def test_profile_scope_migration_uses_matching_profile_not_current(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    database_path = tmp_path / "smart_notes.sqlite3"
    install_fake_migration_profiles(
        monkeypatch,
        tmp_path,
        current_profile="Current Profile",
        profiles={
            "Current Profile": ({111}, {1}),
            "Owning Profile": ({222}, {1}),
        },
    )

    conn = sqlite3.connect(database_path)
    try:
        create_old_unprofiled_smart_field_schema(conn)
        insert_old_text_smart_field(conn, "legacy", 222, 1, "Back", "{{Front}}")
        conn.commit()
        conn.close()

        apply_profile_scope_migration(database_path)

        conn = sqlite3.connect(database_path)
        rows = conn.execute(
            """
            SELECT sf.profile_name, sf.note_type_id, text.prompt_text
            FROM smart_fields sf
            JOIN text_smart_field_settings text ON text.smart_field_id = sf.id
            """
        ).fetchall()

        assert rows == [("Owning Profile", 222, "{{Front}}")]
    finally:
        conn.close()


def test_profile_scope_migration_fails_if_current_profile_is_missing(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    import aqt

    database_path = tmp_path / "smart_notes.sqlite3"
    install_fake_migration_profiles(
        monkeypatch,
        tmp_path,
        current_profile="__test__",
        profiles={"__test__": ({1}, {1})},
    )
    assert aqt.mw is not None
    aqt.mw.pm.name = None

    conn = sqlite3.connect(database_path)
    try:
        create_old_unprofiled_smart_field_schema(conn)
        insert_old_text_smart_field(conn, "legacy", 1, 1, "Back", "{{Front}}")
        conn.commit()
        conn.close()

        with pytest.raises(RuntimeError, match="Anki profile is unavailable"):
            apply_profile_scope_migration(database_path)
    finally:
        conn.close()


def test_profile_scope_migration_clones_global_rows_for_multiple_exact_matches(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    database_path = tmp_path / "smart_notes.sqlite3"
    install_fake_migration_profiles(
        monkeypatch,
        tmp_path,
        current_profile="Profile A",
        profiles={
            "Profile A": ({777}, set()),
            "Profile B": ({777}, set()),
        },
    )

    conn = sqlite3.connect(database_path)
    try:
        create_old_unprofiled_smart_field_schema(conn)
        insert_old_text_smart_field(conn, "legacy", 777, -1, "Back", "{{Front}}")
        conn.commit()
        conn.close()

        apply_profile_scope_migration(database_path)

        conn = sqlite3.connect(database_path)
        rows = conn.execute(
            """
            SELECT sf.id, sf.profile_name, sf.note_type_id, sf.deck_id, text.prompt_text
            FROM smart_fields sf
            JOIN text_smart_field_settings text ON text.smart_field_id = sf.id
            ORDER BY sf.profile_name
            """
        ).fetchall()

        assert [(row[1], row[2], row[3], row[4]) for row in rows] == [
            ("Profile A", 777, -1, "{{Front}}"),
            ("Profile B", 777, -1, "{{Front}}"),
        ]
        assert len({row[0] for row in rows}) == 2
        assert "legacy" in {row[0] for row in rows}
    finally:
        conn.close()


def test_profile_scope_migration_clones_deck_specific_rows_for_multiple_exact_matches(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    database_path = tmp_path / "smart_notes.sqlite3"
    install_fake_migration_profiles(
        monkeypatch,
        tmp_path,
        current_profile="Profile A",
        profiles={
            "Profile A": ({777}, {123}),
            "Profile B": ({777}, {123}),
            "Profile C": ({777}, {456}),
        },
    )

    conn = sqlite3.connect(database_path)
    try:
        create_old_unprofiled_smart_field_schema(conn)
        insert_old_text_smart_field(conn, "legacy", 777, 123, "Back", "{{Front}}")
        conn.commit()
        conn.close()

        apply_profile_scope_migration(database_path)

        conn = sqlite3.connect(database_path)
        rows = conn.execute(
            """
            SELECT sf.profile_name, sf.note_type_id, sf.deck_id, text.prompt_text
            FROM smart_fields sf
            JOIN text_smart_field_settings text ON text.smart_field_id = sf.id
            ORDER BY sf.profile_name
            """
        ).fetchall()

        assert rows == [
            ("Profile A", 777, 123, "{{Front}}"),
            ("Profile B", 777, 123, "{{Front}}"),
        ]
    finally:
        conn.close()


def test_profile_scope_migration_clones_all_setting_table_rows(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    database_path = tmp_path / "smart_notes.sqlite3"
    install_fake_migration_profiles(
        monkeypatch,
        tmp_path,
        current_profile="Profile A",
        profiles={
            "Profile A": ({777}, set()),
            "Profile B": ({777}, set()),
        },
    )

    conn = sqlite3.connect(database_path)
    try:
        create_old_unprofiled_smart_field_schema(conn)
        insert_old_text_smart_field(
            conn, "legacy-text", 777, -1, "TextTarget", "{{Front}}"
        )
        insert_old_tts_smart_field(conn, "legacy-tts", 777, -1, "AudioTarget")
        insert_old_image_smart_field(conn, "legacy-image", 777, -1, "ImageTarget")
        conn.commit()
        conn.close()

        apply_profile_scope_migration(database_path)

        conn = sqlite3.connect(database_path)
        text_rows = conn.execute(
            """
            SELECT sf.profile_name, sf.target_field_name, text.prompt_text, text.model
            FROM smart_fields sf
            JOIN text_smart_field_settings text ON text.smart_field_id = sf.id
            ORDER BY sf.profile_name
            """
        ).fetchall()
        tts_rows = conn.execute(
            """
            SELECT sf.profile_name, sf.target_field_name, tts.source_field_name,
                tts.model, tts.voice_id
            FROM smart_fields sf
            JOIN tts_smart_field_settings tts ON tts.smart_field_id = sf.id
            ORDER BY sf.profile_name
            """
        ).fetchall()
        image_rows = conn.execute(
            """
            SELECT sf.profile_name, sf.target_field_name, image.prompt_text, image.model
            FROM smart_fields sf
            JOIN image_smart_field_settings image ON image.smart_field_id = sf.id
            ORDER BY sf.profile_name
            """
        ).fetchall()

        assert text_rows == [
            ("Profile A", "TextTarget", "{{Front}}", "gpt-5-mini"),
            ("Profile B", "TextTarget", "{{Front}}", "gpt-5-mini"),
        ]
        assert tts_rows == [
            ("Profile A", "AudioTarget", "Front", "tts-1", "alloy"),
            ("Profile B", "AudioTarget", "Front", "tts-1", "alloy"),
        ]
        assert image_rows == [
            ("Profile A", "ImageTarget", "draw {{Front}}", "gpt-image-1.5-low"),
            ("Profile B", "ImageTarget", "draw {{Front}}", "gpt-image-1.5-low"),
        ]
    finally:
        conn.close()


def test_profile_scope_migration_skips_rows_without_confident_profile_match(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    caplog: pytest.LogCaptureFixture,
) -> None:
    database_path = tmp_path / "smart_notes.sqlite3"
    install_fake_migration_profiles(
        monkeypatch,
        tmp_path,
        profiles={"__test__": ({1}, {1})},
    )
    caplog.set_level("WARNING", logger="smart_notes")

    conn = sqlite3.connect(database_path)
    try:
        create_old_unprofiled_smart_field_schema(conn)
        insert_old_text_smart_field(conn, "orphan", 999, 1, "Back", "{{Front}}")
        conn.commit()
        conn.close()

        apply_profile_scope_migration(database_path)

        conn = sqlite3.connect(database_path)

        assert conn.execute("SELECT count(*) FROM smart_fields").fetchone()[0] == 0
        assert (
            conn.execute("SELECT count(*) FROM text_smart_field_settings").fetchone()[0]
            == 0
        )
        assert "skipping unprofiled smart field id=orphan" in caplog.text
    finally:
        conn.close()


def test_get_database_path_uses_anki_preserved_user_files() -> None:
    assert get_database_path().endswith("/user_files/smart_notes.sqlite3")
    assert "/src/user_files/" not in get_database_path()


def create_old_unprofiled_smart_field_schema(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE smart_fields (
            id TEXT PRIMARY KEY,
            note_type_id INTEGER NOT NULL,
            deck_id INTEGER NOT NULL,
            target_field_name TEXT NOT NULL,
            field_type TEXT NOT NULL CHECK (field_type IN ('chat', 'tts', 'image')),
            enabled INTEGER NOT NULL DEFAULT 1 CHECK (enabled IN (0, 1)),
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            UNIQUE(note_type_id, deck_id, target_field_name)
        );
        """
    )
    conn.execute(
        """
        CREATE TABLE text_smart_field_settings (
            smart_field_id TEXT PRIMARY KEY REFERENCES smart_fields(id) ON DELETE CASCADE,
            prompt_text TEXT NOT NULL,
            uses_default_generation_settings INTEGER NOT NULL DEFAULT 1 CHECK (uses_default_generation_settings IN (0, 1)),
            provider TEXT,
            model TEXT,
            reasoning_level TEXT CHECK (reasoning_level IN ('off', 'low', 'high')),
            web_search_enabled INTEGER CHECK (web_search_enabled IN (0, 1))
        );
        """
    )
    conn.execute(
        """
        CREATE TABLE tts_smart_field_settings (
            smart_field_id TEXT PRIMARY KEY REFERENCES smart_fields(id) ON DELETE CASCADE,
            source_field_name TEXT NOT NULL,
            uses_default_generation_settings INTEGER NOT NULL DEFAULT 1 CHECK (uses_default_generation_settings IN (0, 1)),
            provider TEXT,
            model TEXT,
            voice_id TEXT
        );
        """
    )
    conn.execute(
        """
        CREATE TABLE image_smart_field_settings (
            smart_field_id TEXT PRIMARY KEY REFERENCES smart_fields(id) ON DELETE CASCADE,
            prompt_text TEXT NOT NULL,
            uses_default_generation_settings INTEGER NOT NULL DEFAULT 1 CHECK (uses_default_generation_settings IN (0, 1)),
            provider TEXT,
            model TEXT
        );
        """
    )


def insert_old_text_smart_field(
    conn: sqlite3.Connection,
    smart_field_id: str,
    note_type_id: int,
    deck_id: int,
    target_field: str,
    prompt: str,
) -> None:
    insert_old_smart_field(
        conn, smart_field_id, note_type_id, deck_id, target_field, "chat"
    )
    conn.execute(
        """
        INSERT INTO text_smart_field_settings (
            smart_field_id, prompt_text, uses_default_generation_settings,
            provider, model, reasoning_level, web_search_enabled
        )
        VALUES (?, ?, 0, 'openai', 'gpt-5-mini', 'off', 0)
        """,
        (smart_field_id, prompt),
    )


def insert_old_tts_smart_field(
    conn: sqlite3.Connection,
    smart_field_id: str,
    note_type_id: int,
    deck_id: int,
    target_field: str,
) -> None:
    insert_old_smart_field(
        conn, smart_field_id, note_type_id, deck_id, target_field, "tts"
    )
    conn.execute(
        """
        INSERT INTO tts_smart_field_settings (
            smart_field_id, source_field_name, uses_default_generation_settings,
            provider, model, voice_id
        )
        VALUES (?, 'Front', 0, 'openai', 'tts-1', 'alloy')
        """,
        (smart_field_id,),
    )


def insert_old_image_smart_field(
    conn: sqlite3.Connection,
    smart_field_id: str,
    note_type_id: int,
    deck_id: int,
    target_field: str,
) -> None:
    insert_old_smart_field(
        conn, smart_field_id, note_type_id, deck_id, target_field, "image"
    )
    conn.execute(
        """
        INSERT INTO image_smart_field_settings (
            smart_field_id, prompt_text, uses_default_generation_settings,
            provider, model
        )
        VALUES (?, 'draw {{Front}}', 0, 'openai', 'gpt-image-1.5-low')
        """,
        (smart_field_id,),
    )


def insert_old_smart_field(
    conn: sqlite3.Connection,
    smart_field_id: str,
    note_type_id: int,
    deck_id: int,
    target_field: str,
    field_type: str,
) -> None:
    conn.execute(
        """
        INSERT INTO smart_fields (
            id, note_type_id, deck_id, target_field_name, field_type,
            enabled, created_at, updated_at
        )
        VALUES (?, ?, ?, ?, ?, 1, 'now', 'now')
        """,
        (smart_field_id, note_type_id, deck_id, target_field, field_type),
    )


def apply_profile_scope_migration(database_path: Path) -> None:
    migrations_path = Path(__file__).parents[1] / "src" / "database" / "db_migrations"
    migrations = read_migrations(str(migrations_path))
    backend = get_sqlite_backend(str(database_path))
    with backend.lock():
        backend.apply_migrations(migrations[2:3])


def install_fake_migration_profiles(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    *,
    profiles: dict[str, tuple[set[int], set[int]]],
    current_profile: str = "__test__",
) -> None:
    import anki.collection
    import aqt

    install_fake_profile_collections(
        monkeypatch,
        tmp_path,
        profiles={
            name: profile_data(
                {f"Note Type {note_type_id}": note_type_id for note_type_id in ids},
                deck_ids,
            )
            for name, (ids, deck_ids) in profiles.items()
        },
        current_profile=current_profile,
        modules_with_mw=(aqt,),
        modules_with_collection=(anki.collection,),
    )
