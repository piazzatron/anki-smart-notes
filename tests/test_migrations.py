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

from typing import Optional

import pytest

from src.migrations import run_migrations


def test_run_migrations_applies_schema_before_legacy_config_import(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[str] = []

    def apply_database_migrations(migration_count: Optional[int] = None) -> None:
        calls.append(f"database:{migration_count}")

    monkeypatch.setattr(
        "src.migrations.apply_database_migrations", apply_database_migrations
    )
    monkeypatch.setattr(
        "src.migrations.migrate_legacy_smart_field_config",
        lambda: calls.append("legacy_config"),
    )

    run_migrations()

    assert calls == ["database:1", "legacy_config", "database:None"]
