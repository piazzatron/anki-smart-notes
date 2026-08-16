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

import src.web_app as web_app


def test_local_server_starts_once(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[str] = []

    class FakeLocalServer:
        def __init__(self) -> None:
            calls.append("server_init")

        def start(self) -> None:
            calls.append("server_start")

    monkeypatch.setattr(web_app, "_local_server", None)
    monkeypatch.setattr(web_app, "LocalServer", FakeLocalServer)
    monkeypatch.setattr(web_app, "migrate_config", lambda: calls.append("migrate"))

    web_app.ensure_local_server_started()
    web_app.ensure_local_server_started()

    assert calls == ["migrate", "server_init", "server_start"]


def test_open_web_app_refreshes_account(monkeypatch: pytest.MonkeyPatch) -> None:
    server = SimpleNamespace(session_token="session-token")
    dialog = MagicMock()
    dialog_factory = MagicMock(return_value=dialog)
    account_state = MagicMock()
    monkeypatch.setattr(web_app, "_local_server", server)
    monkeypatch.setattr(web_app, "_web_app_dialog", None)
    monkeypatch.setattr(web_app, "ensure_local_server_started", lambda: server)
    monkeypatch.setattr(web_app, "app_state", account_state)
    monkeypatch.setattr(web_app, "WebAppDialog", dialog_factory)
    monkeypatch.setattr(web_app.env, "environment", "DEV")

    web_app.open_web_app()

    account_state.update_account_state.assert_called_once_with()
    dialog_factory.assert_called_once_with(web_app.WEB_APP_DEV_URL, web_app.mw)
    dialog.finished.connect.assert_called_once_with(ANY)
    dialog.show.assert_called_once_with()


def test_open_web_app_raises_existing_dialog(monkeypatch: pytest.MonkeyPatch) -> None:
    server = SimpleNamespace(session_token="session-token")
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
