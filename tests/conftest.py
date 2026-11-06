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

import os
from pathlib import Path

import pytest

os.environ["IS_TEST"] = "True"

import src.app_state as _  # noqa: E402, F401


@pytest.fixture(autouse=True)
def current_profile_name(monkeypatch: pytest.MonkeyPatch) -> None:
    import src.utils

    monkeypatch.setattr(src.utils, "get_current_profile_name", lambda: "__test__")


@pytest.fixture(autouse=True)
def install_id(monkeypatch: pytest.MonkeyPatch) -> None:
    # The real one reads and writes Anki's add-on config.
    import src.api_client
    import src.local_server

    for module in (src.api_client, src.local_server):
        monkeypatch.setattr(module, "get_install_id", lambda: "test-install-id")


@pytest.fixture(scope="session")
def migrated_database(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """A fully migrated smart notes database, built once per session for tests to copy."""
    from src.database.migrations import apply_database_migrations

    path = tmp_path_factory.mktemp("template") / "smart_notes.sqlite3"
    apply_database_migrations(str(path))
    return path
