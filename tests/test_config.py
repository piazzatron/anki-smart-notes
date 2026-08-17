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

from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest


def test_bump_usage_counter_shows_rate_dialog_for_paid_user(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import src.app_state
    import src.config
    import src.ui.rate_dialog

    test_config = SimpleNamespace(times_used=20, did_show_rate_dialog=False)
    dialog = MagicMock()
    monkeypatch.setattr(src.config, "config", test_config)
    monkeypatch.setattr(
        src.app_state,
        "app_state",
        SimpleNamespace(state={"status": "AUTHENTICATED"}),
    )
    monkeypatch.setattr(
        src.ui.rate_dialog, "RateDialog", MagicMock(return_value=dialog)
    )

    src.config.bump_usage_counter()

    assert test_config.times_used == 21
    assert test_config.did_show_rate_dialog is True
    dialog.exec.assert_called_once_with()
