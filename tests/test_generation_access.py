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

from unittest.mock import MagicMock

import pytest

import src.generation_access as generation_access


def test_generation_rejection_rechecks_availability_after_refresh(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    account_state = MagicMock()
    ensure_available = MagicMock(return_value=False)
    monkeypatch.setattr(generation_access, "app_state", account_state)
    monkeypatch.setattr(
        generation_access,
        "ensure_generation_available",
        ensure_available,
    )

    generation_access.refresh_account_after_generation_rejected()

    on_updated = account_state.update_account_state.call_args.kwargs["on_updated"]
    on_updated(account_state.state)
    ensure_available.assert_called_once_with()
