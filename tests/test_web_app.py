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
from unittest.mock import ANY, MagicMock

import pytest

import src.local_server as local_server
import src.ui.app_windows as app_windows
import src.web_app as web_app
from src.event_bus import ScreenRequested


def test_local_server_starts_once(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[str] = []

    class FakeLocalServer:
        def __init__(self) -> None:
            calls.append("server_init")

        def start(self) -> None:
            calls.append("server_start")

    monkeypatch.setattr(local_server, "_local_server", None)
    monkeypatch.setattr(local_server, "LocalServer", FakeLocalServer)

    local_server.ensure_local_server_started()
    local_server.ensure_local_server_started()

    assert calls == ["server_init", "server_start"]


def test_dev_web_app_url_carries_the_requested_screen(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(local_server.env, "environment", "DEV")

    assert local_server.web_app_url() == local_server.WEB_APP_DEV_URL
    assert local_server.web_app_url("chat-settings").endswith("?screen=chat-settings")


@pytest.mark.parametrize(
    ("language", "expected_locale"),
    [("pt-BR", "pt-BR"), ("auto", "ja")],
)
def test_production_web_app_url_uses_effective_locale(
    monkeypatch: pytest.MonkeyPatch, language: str, expected_locale: str
) -> None:
    monkeypatch.setattr(
        local_server, "_local_server", SimpleNamespace(session_token="session-token")
    )
    monkeypatch.setattr(local_server.env, "environment", "PROD")
    monkeypatch.setattr(local_server, "config", SimpleNamespace(language=language))
    monkeypatch.setattr(local_server.lang, "current_lang", "ja")

    assert local_server.web_app_url() == (
        "http://127.0.0.1:8766/app?token=session-token"
        f"&locale={expected_locale}&ankiLocale=ja"
    )


def test_open_web_app_refreshes_account(monkeypatch: pytest.MonkeyPatch) -> None:
    account_state = MagicMock()
    opener = MagicMock()
    monkeypatch.setattr(web_app, "is_local_server_started", lambda: True)
    monkeypatch.setattr(web_app, "ensure_local_server_started", MagicMock())
    monkeypatch.setattr(web_app, "web_app_url", lambda screen: "http://app")
    monkeypatch.setattr(web_app, "app_state", account_state)
    monkeypatch.setattr(web_app, "open_web_app_window", opener)

    web_app.open_web_app()

    account_state.update_account_state.assert_called_once_with()
    opener.assert_called_once_with("http://app", None)


def test_open_web_app_window_creates_a_dialog(monkeypatch: pytest.MonkeyPatch) -> None:
    dialog = MagicMock()
    dialog_factory = MagicMock(return_value=dialog)
    monkeypatch.setattr(app_windows, "_web_app_dialog", None)
    monkeypatch.setattr(app_windows, "WebAppDialog", dialog_factory)

    app_windows.open_web_app_window("http://app")

    dialog_factory.assert_called_once_with("http://app", app_windows.mw)
    dialog.finished.connect.assert_called_once_with(ANY)
    dialog.show.assert_called_once_with()


def test_open_web_app_window_raises_and_navigates_an_open_dialog(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    dialog = MagicMock()
    dialog_factory = MagicMock()
    published = []
    monkeypatch.setattr(app_windows, "_web_app_dialog", dialog)
    monkeypatch.setattr(app_windows, "WebAppDialog", dialog_factory)
    monkeypatch.setattr(app_windows.event_bus, "publish", published.append)

    app_windows.open_web_app_window("http://app", "chat-settings")

    dialog.raise_.assert_called_once_with()
    dialog.activateWindow.assert_called_once_with()
    dialog_factory.assert_not_called()
    assert published == [ScreenRequested(screen="chat-settings")]


def test_close_web_app_closes_dialog(monkeypatch: pytest.MonkeyPatch) -> None:
    dialog = MagicMock()
    monkeypatch.setattr(app_windows, "_web_app_dialog", dialog)

    app_windows.close_web_app()
    app_windows.close_web_app()

    dialog.close.assert_called_once_with()
