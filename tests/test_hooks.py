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

import sys
from types import SimpleNamespace
from typing import Any, cast

import pytest

import src.hooks as hooks
from src.note_proccessor import NoteProcessor


def test_profile_did_open_restarts_local_server_after_profile_switch(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[str] = []

    class FakeLocalServer:
        def __init__(self) -> None:
            calls.append("server_init")

        def start(self) -> None:
            calls.append("server_start")

    monkeypatch.setattr(hooks, "_local_server", None)
    monkeypatch.setitem(
        sys.modules,
        "src.local_server",
        SimpleNamespace(LocalServer=FakeLocalServer),
    )

    hooks.on_profile_did_open()
    hooks.on_profile_did_open()

    assert calls == [
        "server_init",
        "server_start",
    ]


def test_profile_did_open_hook_is_registered() -> None:
    assert hasattr(hooks.gui_hooks, "profile_did_open")


def test_profile_cleanup_closes_open_options_dialog(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    did_close = False

    class FakeDialog:
        def close(self) -> None:
            nonlocal did_close
            did_close = True

    monkeypatch.setattr(
        hooks,
        "_open_options_dialog",
        cast(Any, FakeDialog()),
    )

    monkeypatch.setattr(hooks, "_local_server", None)
    monkeypatch.setattr(hooks, "_review_time_evaluator", None)

    hooks.cleanup()

    assert did_close


def test_profile_cleanup_stops_review_time_evaluator(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    did_stop = False

    class FakeReviewTimeEvaluator:
        def stop(self) -> None:
            nonlocal did_stop
            did_stop = True

    monkeypatch.setattr(hooks, "_open_options_dialog", None)
    monkeypatch.setattr(hooks, "_local_server", None)
    monkeypatch.setattr(
        hooks,
        "_review_time_evaluator",
        cast(Any, FakeReviewTimeEvaluator()),
    )
    monkeypatch.setattr(hooks, "cleanup_logger", lambda: None)

    hooks.cleanup()

    assert did_stop
    assert vars(hooks)["_review_time_evaluator"] is None


def test_addon_install_hook_cleans_up_current_addon(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[str] = []
    current_package = hooks.__name__.split(".", maxsplit=1)[0]

    monkeypatch.setattr(
        hooks,
        "_cleanup_before_addon_files_change",
        lambda: calls.append("cleanup"),
    )

    hooks.on_addon_manager_will_install_addon(object(), "other-addon")
    hooks.on_addon_manager_will_install_addon(object(), current_package)

    assert calls == ["cleanup"]


def test_addon_delete_hook_cleans_up_current_addon(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[str] = []
    current_package = hooks.__name__.split(".", maxsplit=1)[0]

    monkeypatch.setattr(
        hooks,
        "_cleanup_before_addon_files_change",
        lambda: calls.append("cleanup"),
    )

    hooks.on_addons_dialog_will_delete_addons(object(), ["first", current_package])

    assert calls == ["cleanup"]


def test_setup_hooks_supports_anki_without_addon_install_hook(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake_gui_hooks = _fake_gui_hooks(
        addons_dialog_will_delete_addons=[],
    )
    monkeypatch.setattr(hooks, "gui_hooks", fake_gui_hooks)

    hooks.setup_hooks(cast(NoteProcessor, object()))

    assert fake_gui_hooks.addons_dialog_will_delete_addons == [
        hooks.on_addons_dialog_will_delete_addons
    ]


def test_setup_hooks_supports_anki_without_addon_cleanup_hooks(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(hooks, "gui_hooks", _fake_gui_hooks())

    hooks.setup_hooks(cast(NoteProcessor, object()))


def test_setup_hooks_registers_available_addon_cleanup_hooks(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake_gui_hooks = _fake_gui_hooks(
        addon_manager_will_install_addon=[],
        addons_dialog_will_delete_addons=[],
    )
    monkeypatch.setattr(hooks, "gui_hooks", fake_gui_hooks)

    hooks.setup_hooks(cast(NoteProcessor, object()))

    assert fake_gui_hooks.addon_manager_will_install_addon == [
        hooks.on_addon_manager_will_install_addon
    ]
    assert fake_gui_hooks.addons_dialog_will_delete_addons == [
        hooks.on_addons_dialog_will_delete_addons
    ]


def test_cleanup_before_addon_files_change_releases_non_ui_resources(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[str] = []

    class FakeLocalServer:
        def stop(self) -> None:
            calls.append("server_stop")

    monkeypatch.setattr(hooks, "_local_server", FakeLocalServer())
    monkeypatch.setattr(hooks.logger, "info", lambda message: calls.append(message))
    monkeypatch.setattr(hooks, "cleanup_logger", lambda: calls.append("logger_cleanup"))

    vars(hooks)["_cleanup_before_addon_files_change"]()

    assert calls == [
        "Preparing Smart Notes for add-on file replacement",
        "Stopping Smart Notes local server before add-on file replacement",
        "server_stop",
        "Closing Smart Notes log handlers before add-on file replacement",
        "logger_cleanup",
    ]
    assert vars(hooks)["_local_server"] is None


def _fake_gui_hooks(**addon_hooks: list[Any]) -> SimpleNamespace:
    return SimpleNamespace(
        browser_will_show_context_menu=[],
        browser_sidebar_will_show_context_menu=[],
        editor_did_init_buttons=[],
        editor_will_show_context_menu=[],
        overview_did_refresh=[],
        reviewer_did_show_question=[],
        reviewer_did_answer_card=[],
        main_window_did_init=[],
        profile_did_open=[],
        profile_will_close=[],
        **addon_hooks,
    )
