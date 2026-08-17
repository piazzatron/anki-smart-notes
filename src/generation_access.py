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

from .app_state import AppState, app_state, is_capacity_remaining_or_legacy
from .web_app import open_web_app


def ensure_generation_available() -> bool:
    """Open the account UI and reject a user-triggered generation when blocked."""
    if is_capacity_remaining_or_legacy():
        return True

    open_generation_blocked_ui()
    return False


def open_generation_blocked_ui() -> None:
    open_web_app()


def refresh_account_after_generation_rejected() -> None:
    """Refresh stale account data before deciding whether to open the account UI."""
    app_state.update_account_state(on_updated=_open_web_app_if_still_blocked)


def _open_web_app_if_still_blocked(_: AppState) -> None:
    ensure_generation_available()
