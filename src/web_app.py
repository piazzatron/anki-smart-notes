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

from .app_state import app_state
from .local_server import (
    assistant_url,
    ensure_local_server_started,
    is_local_server_started,
    web_app_url,
)
from .sentry import with_sentry
from .ui.app_windows import open_assistant_window, open_web_app_window
from .ui.ui_utils import show_message_box

STARTING_UP_MESSAGE = "Smart Notes is still starting up — try again in a moment."


@with_sentry
def open_web_app(screen: Optional[str] = None) -> None:
    if not is_local_server_started():
        show_message_box(STARTING_UP_MESSAGE)
        return

    ensure_local_server_started()
    app_state.update_account_state()
    open_web_app_window(web_app_url(screen), screen)


@with_sentry
def open_assistant() -> None:
    if not is_local_server_started():
        show_message_box(STARTING_UP_MESSAGE)
        return

    ensure_local_server_started()
    app_state.update_account_state()
    open_assistant_window(assistant_url())
