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

from anki import lang
from aqt import mw

from . import env
from .app_state import app_state
from .config import config
from .constants import WEB_APP_DEV_URL
from .event_bus import UpgradeRequested, event_bus
from .local_server import LOCAL_SERVER_HOST, LocalServer
from .logger import logger
from .sentry import with_sentry
from .telemetry import track_event
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
        _local_server = LocalServer()
        _local_server.start()

    return _local_server


@with_sentry
def open_web_app(*, upgrade_feature: Optional[str] = None) -> None:
    """Open or raise the Smart Notes window, optionally on the upgrade sheet for
    a feature the account's plan doesn't include."""
    global _web_app_dialog

    if _local_server is None:
        show_message_box("Smart Notes is still starting up — try again in a moment.")
        return

    local_server = ensure_local_server_started()
    if local_server.port is None:
        show_message_box(
            "Smart Notes couldn't start its local server. Restart Anki and try again."
        )
        return
    app_state.update_account_state()
    if _web_app_dialog is not None:
        _web_app_dialog.raise_()
        _web_app_dialog.activateWindow()
        if upgrade_feature is not None:
            event_bus.publish(UpgradeRequested(upgrade_feature))
        return

    if upgrade_feature is not None:
        event_bus.publish_to_next_subscriber(UpgradeRequested(upgrade_feature))

    # Dev builds always load the Vite dev server for HMR (`cli/sn up web`); the
    # bundled static app is only served in packaged builds.
    if env.environment == "DEV":
        url = WEB_APP_DEV_URL
    else:
        requested_locale = (
            lang.current_lang if config.language == "auto" else config.language
        )
        # The web app's matchCatalogLocale owns locale normalization and fallback.
        url = (
            f"http://{LOCAL_SERVER_HOST}:{local_server.port}/app"
            f"?token={local_server.session_token}"
            f"&locale={requested_locale}"
            f"&ankiLocale={lang.current_lang}"
        )
    dialog = WebAppDialog(url, mw)
    _web_app_dialog = dialog

    def clear_web_app_dialog(_: object) -> None:
        global _web_app_dialog
        if _web_app_dialog is dialog:
            _web_app_dialog = None

    dialog.finished.connect(clear_web_app_dialog)
    dialog.show()
    # Parented to the main window, it would otherwise open behind the Add or
    # Browser window that triggered it.
    dialog.raise_()
    dialog.activateWindow()
    track_event("smart_notes_window_opened")


def close_web_app() -> None:
    global _web_app_dialog

    if _web_app_dialog is None:
        return

    # Close the webview before its Anki profile state becomes stale. Production
    # sessions also receive a new local API token on the next profile load.
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
