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

import json
import sqlite3
from copy import deepcopy
from pathlib import Path
from typing import Any, Optional, cast

import pytest
from anki.decks import DeckId

from src.database.legacy_config_migration import migrate_legacy_config_to_database
from src.database.migrations import apply_database_bootstrap_migrations
from src.models import DEFAULT_EXTRAS, FieldExtras
from tests.fake_anki_profiles import (
    FakeProfileData,
    install_fake_profile_collections,
    profile_data as fake_profile_data,
)

NOTE_TYPE_ID = 123
DECK_ID = cast(DeckId, 1)
SECOND_PROFILE_NOTE_TYPE_ID = 456


class FakeAddonManager:
    def __init__(self, addon_config: dict[str, Any]) -> None:
        self.addon_config = addon_config
        self.written_config: Optional[dict[str, Any]] = None

    def getConfig(self, addon_name: str) -> dict[str, Any]:
        return self.addon_config

    def writeConfig(self, addon_name: str, addon_config: dict[str, Any]) -> None:
        self.written_config = deepcopy(addon_config)


class FakeConfig:
    def __init__(self, addon_config: dict[str, Any]) -> None:
        self.addon_config = addon_config

    @property
    def did_migrate_smart_fields_to_sqlite(self) -> bool:
        return bool(self.addon_config.get("did_migrate_smart_fields_to_sqlite"))

    def __getattr__(self, key: str) -> object:
        return self.addon_config.get(key)


class FakeSentry:
    def __init__(self) -> None:
        self.captured: list[Exception] = []

    def capture_exception(self, error: Exception) -> None:
        self.captured.append(error)


@pytest.fixture(autouse=True)
def sqlite_database(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    import src.database.connection

    monkeypatch.setattr(
        src.database.connection,
        "get_database_path",
        lambda: str(tmp_path / "smart_notes.sqlite3"),
    )
    apply_database_bootstrap_migrations()


def test_migrate_legacy_smart_field_config_imports_prompts_and_cleans_config(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    addon_config = {
        "prompts_map": {
            "note_types": {
                "Basic": {
                    "1": {
                        "fields": {"Back": "{{Front}}"},
                        "extras": {"Back": chat_extras()},
                    }
                }
            }
        },
        "did_deck_filter_migration": True,
        "did_cleanup_config_defaults": True,
        "did_migrate_smart_fields_to_sqlite": False,
    }
    expected_backup = deepcopy(addon_config)
    fake_mw = install_fake_anki(monkeypatch, addon_config, tmp_path)
    messages: list[tuple[object, ...]] = []
    install_migration_alert(monkeypatch, messages)

    migrate_legacy_config_to_database()

    smart_fields = fetch_legacy_text_smart_fields()
    backup_files = list(
        (tmp_path / "user_files").glob("config_backup_before_sqlite_*.json")
    )

    assert len(smart_fields) == 1
    assert smart_fields[0]["profile_name"] == "__test__"
    assert smart_fields[0]["note_type_id"] == NOTE_TYPE_ID
    assert smart_fields[0]["deck_id"] == int(DECK_ID)
    assert smart_fields[0]["target_field_name"] == "Back"
    assert smart_fields[0]["prompt_text"] == "{{Front}}"
    assert smart_fields[0]["provider"] == "auto"
    assert smart_fields[0]["model"] == "auto"
    assert len(backup_files) == 1
    assert json.loads(backup_files[0].read_text(encoding="utf-8")) == expected_backup
    assert fake_mw.addonManager.written_config is not None
    assert "prompts_map" not in fake_mw.addonManager.written_config
    assert "did_deck_filter_migration" not in fake_mw.addonManager.written_config
    assert "did_cleanup_config_defaults" not in fake_mw.addonManager.written_config
    assert (
        fake_mw.addonManager.written_config["did_migrate_smart_fields_to_sqlite"]
        is True
    )
    assert messages == []


def test_migrate_legacy_smart_field_config_skips_missing_note_types(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    addon_config = {
        "prompts_map": {
            "note_types": {
                "Basic": {
                    "1": {
                        "fields": {"Back": "{{Front}}"},
                        "extras": {"Back": chat_extras()},
                    }
                },
                "Deleted Legacy Type": {
                    "1": {
                        "fields": {"Back": "{{Front}}"},
                        "extras": {"Back": chat_extras()},
                    }
                },
            }
        },
        "did_migrate_smart_fields_to_sqlite": False,
    }
    expected_backup = deepcopy(addon_config)
    fake_mw = install_fake_anki(monkeypatch, addon_config, tmp_path)
    messages: list[tuple[object, ...]] = []
    install_migration_alert(monkeypatch, messages)

    migrate_legacy_config_to_database()

    smart_fields = fetch_legacy_text_smart_fields()
    backup_files = list(
        (tmp_path / "user_files").glob("config_backup_before_sqlite_*.json")
    )

    assert len(smart_fields) == 1
    assert smart_fields[0]["target_field_name"] == "Back"
    assert smart_fields[0]["prompt_text"] == "{{Front}}"
    assert len(backup_files) == 1
    assert json.loads(backup_files[0].read_text(encoding="utf-8")) == expected_backup
    assert fake_mw.addonManager.written_config is not None
    assert "prompts_map" not in fake_mw.addonManager.written_config
    assert (
        fake_mw.addonManager.written_config["did_migrate_smart_fields_to_sqlite"]
        is True
    )
    assert messages == []


def test_migrate_legacy_smart_field_config_imports_shared_note_type_name_across_profiles(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    addon_config = {
        "prompts_map": {
            "note_types": {
                "Basic": {
                    str(DECK_ID): {
                        "fields": {"Back": "{{Front}}"},
                        "extras": {"Back": chat_extras()},
                    }
                }
            }
        },
        "did_migrate_smart_fields_to_sqlite": False,
    }
    install_fake_anki(
        monkeypatch,
        addon_config,
        tmp_path,
        profiles={
            "__test__": profile_data({"Basic": NOTE_TYPE_ID}, {int(DECK_ID)}),
            "Second Profile": profile_data(
                {"Basic": SECOND_PROFILE_NOTE_TYPE_ID}, {int(DECK_ID)}
            ),
            "Profile Without Basic": profile_data({"Cloze": 789}, {int(DECK_ID)}),
        },
    )
    install_migration_alert(monkeypatch, [])

    migrate_legacy_config_to_database()

    smart_fields = fetch_legacy_text_smart_fields()

    assert [
        (
            row["profile_name"],
            row["note_type_id"],
            row["deck_id"],
            row["target_field_name"],
            row["prompt_text"],
        )
        for row in smart_fields
    ] == [
        (
            "Second Profile",
            SECOND_PROFILE_NOTE_TYPE_ID,
            int(DECK_ID),
            "Back",
            "{{Front}}",
        ),
        ("__test__", NOTE_TYPE_ID, int(DECK_ID), "Back", "{{Front}}"),
    ]


def test_migrate_legacy_smart_field_config_imports_global_rows_for_each_matching_profile(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    addon_config = {
        "prompts_map": {
            "note_types": {
                "Basic": {
                    "-1": {
                        "fields": {"Summary": "{{Front}}"},
                        "extras": {"Summary": chat_extras()},
                    }
                }
            }
        },
        "did_migrate_smart_fields_to_sqlite": False,
    }
    install_fake_anki(
        monkeypatch,
        addon_config,
        tmp_path,
        profiles={
            "__test__": profile_data({"Basic": NOTE_TYPE_ID}, set()),
            "Second Profile": profile_data(
                {"Basic": SECOND_PROFILE_NOTE_TYPE_ID}, set()
            ),
        },
    )
    install_migration_alert(monkeypatch, [])

    migrate_legacy_config_to_database()

    smart_fields = fetch_legacy_text_smart_fields()

    assert [
        (row["profile_name"], row["note_type_id"], row["deck_id"])
        for row in smart_fields
    ] == [
        ("Second Profile", SECOND_PROFILE_NOTE_TYPE_ID, -1),
        ("__test__", NOTE_TYPE_ID, -1),
    ]


def test_migrate_legacy_smart_field_config_logs_and_skips_missing_deck_for_profile(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    caplog: pytest.LogCaptureFixture,
) -> None:
    addon_config = {
        "prompts_map": {
            "note_types": {
                "Basic": {
                    str(DECK_ID): {
                        "fields": {"Back": "{{Front}}"},
                        "extras": {"Back": chat_extras()},
                    }
                }
            }
        },
        "did_migrate_smart_fields_to_sqlite": False,
    }
    install_fake_anki(
        monkeypatch,
        addon_config,
        tmp_path,
        profiles={
            "__test__": profile_data({"Basic": NOTE_TYPE_ID}, {int(DECK_ID)}),
            "Second Profile": profile_data(
                {"Basic": SECOND_PROFILE_NOTE_TYPE_ID}, {999}
            ),
        },
    )
    install_migration_alert(monkeypatch, [])

    migrate_legacy_config_to_database()

    smart_fields = fetch_legacy_text_smart_fields()

    assert [(row["profile_name"], row["note_type_id"]) for row in smart_fields] == [
        ("__test__", NOTE_TYPE_ID)
    ]
    assert (
        "skipping legacy smart fields for profile=Second Profile, "
        "note_type=Basic, deck_id=1 because the deck id does not exist in that profile"
        in caplog.text
    )


def test_migrate_legacy_smart_field_config_does_not_use_runtime_service(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    import src.database.legacy_config_migration

    addon_config = {
        "prompts_map": {
            "note_types": {
                "Basic": {
                    "1": {
                        "fields": {"Back": "{{Front}}"},
                        "extras": {"Back": chat_extras()},
                    }
                }
            }
        },
        "did_migrate_smart_fields_to_sqlite": False,
    }
    install_fake_anki(monkeypatch, addon_config, tmp_path)
    install_migration_alert(monkeypatch, [])

    class ForbiddenSmartFieldService:
        def __init__(self, *args: object, **kwargs: object) -> None:
            raise AssertionError("legacy migration must not use SmartFieldService")

    class ForbiddenSmartFieldServiceSingleton:
        def __getattr__(self, name: str) -> object:
            raise AssertionError("legacy migration must not use smart_field_service")

    monkeypatch.setattr(
        src.database.legacy_config_migration,
        "SmartFieldService",
        ForbiddenSmartFieldService,
        raising=False,
    )
    monkeypatch.setattr(
        src.database.legacy_config_migration,
        "smart_field_service",
        ForbiddenSmartFieldServiceSingleton(),
        raising=False,
    )

    migrate_legacy_config_to_database()

    assert len(fetch_legacy_text_smart_fields()) == 1


def test_migrate_legacy_smart_field_config_writes_bootstrap_settings_shape(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    import src.database.connection

    addon_config = {
        "prompts_map": {
            "note_types": {
                "Basic": {
                    "1": {
                        "fields": {
                            "Back": "{{Front}}",
                            "Audio": "{{Front}}",
                            "Image": "draw {{Front}}",
                        },
                        "extras": {
                            "Back": chat_extras(),
                            "Audio": tts_extras(),
                            "Image": image_extras(),
                        },
                    }
                }
            }
        },
        "did_migrate_smart_fields_to_sqlite": False,
    }
    install_fake_anki(monkeypatch, addon_config, tmp_path)
    install_migration_alert(monkeypatch, [])

    migrate_legacy_config_to_database()

    with src.database.connection.open_database() as conn:
        assert table_columns(conn, "smart_fields") == [
            "id",
            "profile_name",
            "note_type_id",
            "deck_id",
            "target_field_name",
            "field_type",
            "enabled",
            "created_at",
            "updated_at",
        ]
        assert table_columns(conn, "text_smart_field_settings") == [
            "smart_field_id",
            "prompt_text",
            "uses_default_generation_settings",
            "provider",
            "model",
            "reasoning_level",
            "web_search_enabled",
        ]
        assert table_columns(conn, "tts_smart_field_settings") == [
            "smart_field_id",
            "source_field_name",
            "uses_default_generation_settings",
            "provider",
            "model",
            "voice_id",
        ]
        assert table_columns(conn, "image_smart_field_settings") == [
            "smart_field_id",
            "prompt_text",
            "uses_default_generation_settings",
            "provider",
            "model",
        ]

        text_row = conn.execute(
            """
            SELECT
                sf.target_field_name,
                text.prompt_text,
                text.uses_default_generation_settings,
                text.provider,
                text.model,
                text.reasoning_level,
                text.web_search_enabled
            FROM smart_fields sf
            JOIN text_smart_field_settings text ON text.smart_field_id = sf.id
            """
        ).fetchone()
        tts_row = conn.execute(
            """
            SELECT
                sf.target_field_name,
                tts.source_field_name,
                tts.uses_default_generation_settings,
                tts.provider,
                tts.model,
                tts.voice_id
            FROM smart_fields sf
            JOIN tts_smart_field_settings tts ON tts.smart_field_id = sf.id
            """
        ).fetchone()
        image_row = conn.execute(
            """
            SELECT
                sf.target_field_name,
                image.prompt_text,
                image.uses_default_generation_settings,
                image.provider,
                image.model
            FROM smart_fields sf
            JOIN image_smart_field_settings image ON image.smart_field_id = sf.id
            """
        ).fetchone()

    assert text_row is not None
    assert tts_row is not None
    assert image_row is not None
    assert tuple(text_row) == ("Back", "{{Front}}", 0, "auto", "auto", "off", 0)
    assert tuple(tts_row) == ("Audio", "Front", 0, "openai", "tts-1", "alloy")
    assert tuple(image_row) == (
        "Image",
        "draw {{Front}}",
        0,
        "openai",
        "gpt-image-1.5-low",
    )


def test_migrate_legacy_smart_field_config_preserves_deprecated_models_for_sql_migration(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    extras = cast(Any, chat_extras())
    extras["chat_provider"] = "openai"
    extras["chat_model"] = "gpt-4o-mini"
    addon_config = {
        "prompts_map": {
            "note_types": {
                "Basic": {
                    "1": {
                        "fields": {"Back": "{{Front}}"},
                        "extras": {"Back": extras},
                    }
                }
            }
        },
        "did_migrate_smart_fields_to_sqlite": False,
    }
    install_fake_anki(monkeypatch, addon_config, tmp_path)
    install_migration_alert(monkeypatch, [])

    migrate_legacy_config_to_database()

    smart_fields = fetch_legacy_text_smart_fields()

    assert len(smart_fields) == 1
    assert smart_fields[0]["provider"] == "openai"
    assert smart_fields[0]["model"] == "gpt-4o-mini"


def test_migrate_legacy_smart_field_config_replaces_prior_failed_attempt_key(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    import src.database.connection

    addon_config = {
        "prompts_map": {
            "note_types": {
                "Basic": {
                    "1": {
                        "fields": {"Back": "{{Front}}"},
                        "extras": {"Back": chat_extras()},
                    }
                }
            }
        },
        "did_migrate_smart_fields_to_sqlite": False,
    }
    install_fake_anki(monkeypatch, addon_config, tmp_path)
    install_migration_alert(monkeypatch, [])

    with src.database.connection.open_database() as conn:
        conn.execute(
            """
            INSERT INTO smart_fields (
                id, profile_name, note_type_id, deck_id, target_field_name, field_type,
                enabled, created_at, updated_at
            )
            VALUES (
                'stale-prior-attempt', '__test__', ?, ?, 'Back', 'chat',
                1, 'now', 'now'
            )
            """,
            (NOTE_TYPE_ID, int(DECK_ID)),
        )
        conn.execute(
            """
            INSERT INTO text_smart_field_settings (
                smart_field_id, prompt_text, uses_default_generation_settings,
                provider, model, reasoning_level, web_search_enabled
            )
            VALUES ('stale-prior-attempt', 'stale', 0, 'openai', 'gpt-5-mini', 'off', 0)
            """
        )
        conn.execute(
            """
            INSERT INTO smart_fields (
                id, profile_name, note_type_id, deck_id, target_field_name, field_type,
                enabled, created_at, updated_at
            )
            VALUES (
                'existing-other-field', '__test__', ?, ?, 'Extra', 'chat',
                1, 'now', 'now'
            )
            """,
            (NOTE_TYPE_ID, int(DECK_ID)),
        )
        conn.execute(
            """
            INSERT INTO text_smart_field_settings (
                smart_field_id, prompt_text, uses_default_generation_settings,
                provider, model, reasoning_level, web_search_enabled
            )
            VALUES (
                'existing-other-field', 'keep me', 0,
                'openai', 'gpt-5-mini', 'off', 0
            )
            """
        )

    migrate_legacy_config_to_database()

    smart_fields = fetch_legacy_text_smart_fields()

    assert [(row["target_field_name"], row["prompt_text"]) for row in smart_fields] == [
        ("Back", "{{Front}}"),
        ("Extra", "keep me"),
    ]


def test_migrate_legacy_smart_field_config_reports_failure_and_keeps_config(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    addon_config = {
        "prompts_map": {
            "note_types": {
                "Basic": {
                    "1": {
                        "fields": {"Audio": "{{Front}} {{Back}}"},
                        "extras": {"Audio": tts_extras()},
                    }
                }
            }
        },
        "did_migrate_smart_fields_to_sqlite": False,
    }
    fake_mw = install_fake_anki(monkeypatch, addon_config, tmp_path)
    messages: list[tuple[object, ...]] = []
    install_migration_alert(monkeypatch, messages)
    fake_sentry = install_fake_sentry(monkeypatch)

    with pytest.raises(ValueError):
        migrate_legacy_config_to_database()

    backup_files = list(
        (tmp_path / "user_files").glob("config_backup_before_sqlite_*.json")
    )

    assert len(backup_files) == 1
    assert fake_mw.addonManager.written_config is None
    assert addon_config["did_migrate_smart_fields_to_sqlite"] is False
    assert "prompts_map" in addon_config
    assert len(fake_sentry.captured) == 1
    assert messages == [
        (
            "Smart Notes could not finish upgrading your Smart Fields.",
            "Please email support@smart-notes.xyz and include your smart-notes.log file.",
        )
    ]


def test_migrate_legacy_smart_field_config_fails_if_current_profile_is_missing(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    import src.utils

    addon_config = {
        "prompts_map": {
            "note_types": {
                "Basic": {
                    "1": {
                        "fields": {"Back": "{{Front}}"},
                        "extras": {"Back": chat_extras()},
                    }
                }
            }
        },
        "did_migrate_smart_fields_to_sqlite": False,
    }
    fake_mw = install_fake_anki(monkeypatch, addon_config, tmp_path)
    messages: list[tuple[object, ...]] = []
    install_migration_alert(monkeypatch, messages)

    def raise_missing_profile() -> str:
        raise RuntimeError("Anki profile is unavailable")

    monkeypatch.setattr(src.utils, "get_current_profile_name", raise_missing_profile)

    with pytest.raises(RuntimeError, match="Anki profile is unavailable"):
        migrate_legacy_config_to_database()

    assert fake_mw.addonManager.written_config is None
    assert addon_config["did_migrate_smart_fields_to_sqlite"] is False
    assert messages == [
        (
            "Smart Notes could not finish upgrading your Smart Fields.",
            "Please email support@smart-notes.xyz and include your smart-notes.log file.",
        )
    ]


def test_migrate_legacy_smart_field_config_does_nothing_after_successful_migration(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    addon_config = {"did_migrate_smart_fields_to_sqlite": True}
    fake_mw = install_fake_anki(monkeypatch, addon_config, tmp_path)

    migrate_legacy_config_to_database()

    assert fake_mw.addonManager.written_config is None
    assert not (tmp_path / "user_files").exists()


def install_fake_anki(
    monkeypatch: pytest.MonkeyPatch,
    addon_config: dict[str, Any],
    tmp_path: Path,
    *,
    profiles: Optional[dict[str, FakeProfileData]] = None,
    current_profile: str = "__test__",
) -> Any:
    import src.database.legacy_config_migration
    import src.smart_field_prompt_map
    import src.utils
    import src.utils.notes_utils

    profile_map = profiles or {
        current_profile: profile_data({"Basic": NOTE_TYPE_ID}, {int(DECK_ID)})
    }
    fake_mw = install_fake_profile_collections(
        monkeypatch,
        tmp_path,
        profiles=profile_map,
        current_profile=current_profile,
        addon_manager=FakeAddonManager(addon_config),
        modules_with_mw=(
            src.database.legacy_config_migration,
            src.smart_field_prompt_map,
            src.utils,
            src.utils.notes_utils,
        ),
        modules_with_collection=(src.database.legacy_config_migration,),
    )
    monkeypatch.setattr(
        src.database.legacy_config_migration, "config", FakeConfig(addon_config)
    )
    monkeypatch.setattr(
        src.database.legacy_config_migration,
        "get_user_files_path",
        lambda filename: str(tmp_path / "user_files" / filename),
    )
    return fake_mw


def fetch_legacy_text_smart_fields() -> list[sqlite3.Row]:
    import src.database.connection

    with src.database.connection.open_database() as conn:
        return list(
            conn.execute(
                """
                SELECT
                    sf.profile_name,
                    sf.note_type_id,
                    sf.deck_id,
                    sf.target_field_name,
                    text.prompt_text,
                    text.provider,
                    text.model
                FROM smart_fields sf
                JOIN text_smart_field_settings text ON text.smart_field_id = sf.id
                ORDER BY sf.profile_name, sf.note_type_id, sf.deck_id, sf.target_field_name
                """
            ).fetchall()
        )


def table_columns(conn: sqlite3.Connection, table: str) -> list[str]:
    return [
        str(row["name"])
        for row in conn.execute(f"PRAGMA table_info({table})").fetchall()
    ]


def profile_data(note_types: dict[str, int], deck_ids: set[int]) -> FakeProfileData:
    return fake_profile_data(note_types, deck_ids)


def install_migration_alert(
    monkeypatch: pytest.MonkeyPatch, messages: list[tuple[object, ...]]
) -> None:
    import src.database.legacy_config_migration

    monkeypatch.setattr(
        src.database.legacy_config_migration,
        "show_message_box",
        lambda *args: messages.append(args),
    )


def install_fake_sentry(monkeypatch: pytest.MonkeyPatch) -> FakeSentry:
    import src.sentry

    fake_sentry = FakeSentry()
    monkeypatch.setattr(src.sentry, "sentry", fake_sentry)
    return fake_sentry


def chat_extras() -> FieldExtras:
    extras = deepcopy(DEFAULT_EXTRAS)
    extras["use_custom_model"] = True
    extras["chat_provider"] = "auto"
    extras["chat_model"] = "auto"
    extras["chat_reasoning_level"] = "off"
    extras["chat_web_search"] = False
    return extras


def tts_extras() -> FieldExtras:
    extras = deepcopy(DEFAULT_EXTRAS)
    extras["type"] = "tts"
    extras["use_custom_model"] = True
    extras["tts_provider"] = "openai"
    extras["tts_model"] = "tts-1"
    extras["tts_voice"] = "alloy"
    return extras


def image_extras() -> FieldExtras:
    extras = deepcopy(DEFAULT_EXTRAS)
    extras["type"] = "image"
    extras["use_custom_model"] = True
    extras["image_provider"] = "openai"
    extras["image_model"] = "gpt-image-1.5-low"
    return extras
