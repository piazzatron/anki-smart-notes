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

from aqt import mw

from . import env
from .app_state import app_state
from .config import migrate_config
from .constants import WEB_APP_DEV_URL
from .local_server import LOCAL_SERVER_HOST, LOCAL_SERVER_PORT, LocalServer
from .logger import logger
from .sentry import with_sentry
from .ui.ui_utils import show_message_box
from .ui.web_app_dialog import WebAppDialog

_local_server: Optional[LocalServer] = None
_web_app_dialog: Optional[WebAppDialog] = None


def ensure_local_server_started() -> LocalServer:
    global _local_server

    # profile_did_open fires before main_window_did_init at startup, so a
    # server usually exists already. Starting another would fail to bind and
    # clobber _local_server with a dead instance (whose session token the
    # webview would then use).
    if _local_server is None:
        migrate_config()
        _local_server = LocalServer()
        _local_server.start()

    return _local_server


@with_sentry
def open_web_app() -> None:
    global _web_app_dialog

    if _local_server is None:
        show_message_box("Smart Notes is still starting up — try again in a moment.")
        return

    local_server = ensure_local_server_started()
    app_state.update_account_state()
    if _web_app_dialog is not None:
        _web_app_dialog.raise_()
        _web_app_dialog.activateWindow()
        return

    # Dev builds always load the Vite dev server for HMR (`make web`); the
    # bundled static app is only served in packaged builds.
    if env.environment == "DEV":
        base_url = WEB_APP_DEV_URL
    else:
        base_url = f"http://{LOCAL_SERVER_HOST}:{LOCAL_SERVER_PORT}/app"
    url = f"{base_url}?token={local_server.session_token}"
    dialog = WebAppDialog(url, mw)
    _web_app_dialog = dialog

    def clear_web_app_dialog(_: object) -> None:
        global _web_app_dialog
        if _web_app_dialog is dialog:
            _web_app_dialog = None

    dialog.finished.connect(clear_web_app_dialog)
    dialog.show()


def close_web_app() -> None:
    global _web_app_dialog

    if _web_app_dialog is None:
        return

    # The local session token changes on profile load, so close the webview
    # before its token becomes stale.
    logger.info("Closing Smart Notes web app before profile close")
    dialog = _web_app_dialog
    _web_app_dialog = None
    dialog.close()


def stop_local_server() -> None:
    global _local_server

    if _local_server is None:
        return

    _local_server.stop()
    _local_server = None
