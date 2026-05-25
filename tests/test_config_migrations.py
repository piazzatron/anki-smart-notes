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

from copy import deepcopy
from typing import Any, Optional

import pytest

from src.config_migrations import migrate_legacy_addon_config


class FakeAddonManager:
    def __init__(self, addon_config: dict[str, Any]) -> None:
        self.addon_config = addon_config
        self.written_config: Optional[dict[str, Any]] = None

    def getConfig(self, addon_name: str) -> dict[str, Any]:
        return self.addon_config

    def writeConfig(self, addon_name: str, addon_config: dict[str, Any]) -> None:
        self.written_config = deepcopy(addon_config)


class FakeMw:
    def __init__(self, addon_config: dict[str, Any]) -> None:
        self.addonManager = FakeAddonManager(addon_config)


def test_migrate_legacy_addon_config_updates_deprecated_chat_defaults(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import src.config_migrations

    addon_config = {
        "chat_provider": "deepseek",
        "chat_model": "deepseek-v3",
    }
    fake_mw = FakeMw(addon_config)
    monkeypatch.setattr(src.config_migrations, "mw", fake_mw)

    migrate_legacy_addon_config()

    assert fake_mw.addonManager.written_config is not None
    assert fake_mw.addonManager.written_config["chat_provider"] == "auto"
    assert fake_mw.addonManager.written_config["chat_model"] == "auto"
