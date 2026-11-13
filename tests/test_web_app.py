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

# pyright: reportPrivateUsage=false

from types import SimpleNamespace
from unittest.mock import ANY, MagicMock

import pytest

import src.ui.web_app_dialog as web_app_dialog
import src.web_app as web_app
from src.local_server import WindowLoad


def test_local_server_starts_once(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[str] = []

    class FakeLocalServer:
        def __init__(self) -> None:
            calls.append("server_init")

        def start(self) -> None:
            calls.append("server_start")

    monkeypatch.setattr(web_app, "_local_server", None)
    monkeypatch.setattr(web_app, "LocalServer", FakeLocalServer)

    web_app.ensure_local_server_started()
    web_app.ensure_local_server_started()

    assert calls == ["server_init", "server_start"]


def test_open_web_app_refreshes_account(monkeypatch: pytest.MonkeyPatch) -> None:
    server = SimpleNamespace(
        session_token="session-token", port=24766, watch_window_load=WindowLoad
    )
    dialog = MagicMock()
    dialog_factory = MagicMock(return_value=dialog)
    account_state = MagicMock()
    monkeypatch.setattr(web_app, "_local_server", server)
    monkeypatch.setattr(web_app, "_web_app_dialog", None)
    monkeypatch.setattr(web_app, "ensure_local_server_started", lambda: server)
    monkeypatch.setattr(web_app, "app_state", account_state)
    monkeypatch.setattr(web_app, "WebAppDialog", dialog_factory)
    monkeypatch.setattr(web_app.env, "environment", "DEV")
    tracked_events: list[str] = []
    monkeypatch.setattr(web_app, "track_event", tracked_events.append)
    monkeypatch.setattr(web_app, "QTimer", MagicMock())

    web_app.open_web_app()

    account_state.update_account_state.assert_called_once_with()
    dialog_factory.assert_called_once_with(web_app.WEB_APP_DEV_URL, web_app.mw)
    dialog.finished.connect.assert_called_once_with(ANY)
    dialog.show.assert_called_once_with()
    assert tracked_events == ["smart_notes_window_opened"]


@pytest.mark.parametrize(
    ("language", "expected_locale"),
    [("pt-BR", "pt-BR"), ("auto", "ja")],
)
def test_production_web_app_url_uses_effective_locale(
    monkeypatch: pytest.MonkeyPatch, language: str, expected_locale: str
) -> None:
    # An OS-picked fallback port: the URL must use whichever port bound.
    server = SimpleNamespace(
        session_token="session-token", port=51234, watch_window_load=WindowLoad
    )
    dialog_factory = MagicMock(return_value=MagicMock())
    monkeypatch.setattr(web_app, "_local_server", server)
    monkeypatch.setattr(web_app, "_web_app_dialog", None)
    monkeypatch.setattr(web_app, "ensure_local_server_started", lambda: server)
    monkeypatch.setattr(web_app, "app_state", MagicMock())
    monkeypatch.setattr(web_app, "WebAppDialog", dialog_factory)
    monkeypatch.setattr(web_app.env, "environment", "PROD")
    monkeypatch.setattr(web_app, "config", SimpleNamespace(language=language))
    monkeypatch.setattr(web_app.lang, "current_lang", "ja")
    monkeypatch.setattr(web_app, "track_event", MagicMock())
    monkeypatch.setattr(web_app, "QTimer", MagicMock())

    web_app.open_web_app()

    dialog_factory.assert_called_once_with(
        "http://127.0.0.1:51234/app?token=session-token"
        f"&locale={expected_locale}&ankiLocale=ja",
        web_app.mw,
    )


def test_open_web_app_raises_existing_dialog(monkeypatch: pytest.MonkeyPatch) -> None:
    server = SimpleNamespace(session_token="session-token", port=24766)
    dialog = MagicMock()
    dialog_factory = MagicMock()
    monkeypatch.setattr(web_app, "_local_server", server)
    monkeypatch.setattr(web_app, "_web_app_dialog", dialog)
    monkeypatch.setattr(web_app, "ensure_local_server_started", lambda: server)
    monkeypatch.setattr(web_app, "app_state", MagicMock())
    monkeypatch.setattr(web_app, "WebAppDialog", dialog_factory)

    web_app.open_web_app()

    dialog.raise_.assert_called_once_with()
    dialog.activateWindow.assert_called_once_with()
    dialog_factory.assert_not_called()


def test_close_web_app_closes_dialog(monkeypatch: pytest.MonkeyPatch) -> None:
    dialog = MagicMock()
    monkeypatch.setattr(web_app, "_web_app_dialog", dialog)

    web_app.close_web_app()
    web_app.close_web_app()

    dialog.close.assert_called_once_with()


def test_web_ui_errors_reach_sentry_without_the_session_token(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    errors: list[str] = []
    monkeypatch.setattr(web_app_dialog.logger, "error", errors.append)
    levels = web_app_dialog.QWebEnginePage.JavaScriptConsoleMessageLevel
    page_url = "http://127.0.0.1:24766/app?token=secret-token&locale=en"

    log = web_app_dialog._SmartNotesWebPage.javaScriptConsoleMessage
    log(MagicMock(), levels.WarningMessageLevel, "a warning", 1, page_url)
    log(MagicMock(), levels.ErrorMessageLevel, "Uncaught TypeError: x", 3, page_url)

    assert errors == ["Web UI error: Uncaught TypeError: x (/app:3)"]


@pytest.mark.parametrize(
    ("connected", "still_open", "reported"),
    [(False, True, True), (True, True, False), (False, False, False)],
)
def test_window_that_never_connects_is_reported_once_while_open(
    monkeypatch: pytest.MonkeyPatch, connected: bool, still_open: bool, reported: bool
) -> None:
    load = WindowLoad(app_requests=["/app/assets/index.js 200"], connected=connected)
    server = SimpleNamespace(
        session_token="session-token", port=24766, watch_window_load=lambda: load
    )
    errors: list[tuple[object, ...]] = []
    monkeypatch.setattr(web_app, "_local_server", server)
    monkeypatch.setattr(web_app, "_web_app_dialog", None)
    monkeypatch.setattr(web_app, "ensure_local_server_started", lambda: server)
    monkeypatch.setattr(web_app, "app_state", MagicMock())
    monkeypatch.setattr(web_app, "WebAppDialog", MagicMock(return_value=MagicMock()))
    monkeypatch.setattr(web_app.env, "environment", "DEV")
    monkeypatch.setattr(web_app, "track_event", MagicMock())
    monkeypatch.setattr(web_app, "supportText", lambda: "Anki 26.09.3")
    monkeypatch.setattr(web_app, "QWebEngineProfile", MagicMock())
    qtimer = MagicMock()
    monkeypatch.setattr(web_app, "QTimer", qtimer)
    monkeypatch.setattr(web_app.logger, "error", lambda *args: errors.append(args))

    web_app.open_web_app()
    if not still_open:
        web_app.close_web_app()
    _, check = qtimer.singleShot.call_args.args
    check()

    assert len(errors) == (1 if reported else 0)
    if reported:
        assert "/app/assets/index.js 200" in str(errors[0])
