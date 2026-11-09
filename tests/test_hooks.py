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
from typing import Any, cast
from unittest.mock import MagicMock

import pytest

import src.hooks as hooks
from src.note_proccessor import NoteProcessor


@pytest.fixture(autouse=True)
def fake_note_will_be_added(monkeypatch: pytest.MonkeyPatch) -> list[Any]:
    # Keep setup_hooks from registering on Anki's real module-level hook.
    hook: list[Any] = []
    monkeypatch.setattr(hooks, "note_will_be_added", hook)
    return hook


def test_profile_switch_restarts_local_server_and_background_generation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    ensure_started = MagicMock()
    monkeypatch.setattr(hooks, "ensure_local_server_started", ensure_started)
    monkeypatch.setattr(hooks, "close_web_app", MagicMock())
    monkeypatch.setattr(hooks, "stop_local_server", MagicMock())
    monkeypatch.setattr(hooks, "_review_time_evaluator", None)
    monkeypatch.setattr(hooks, "_add_time_evaluator", None)
    on_profile_did_open = hooks.on_profile_did_open(cast(NoteProcessor, object()))

    on_profile_did_open()
    first_add_time_evaluator = vars(hooks)["_add_time_evaluator"]
    hooks.cleanup()
    on_profile_did_open()

    assert ensure_started.call_count == 2
    assert first_add_time_evaluator is not None
    assert first_add_time_evaluator.is_stopped
    for name in ("_review_time_evaluator", "_add_time_evaluator"):
        evaluator = vars(hooks)[name]
        assert evaluator is not None
        assert not evaluator.is_stopped


def test_profile_cleanup_closes_open_web_app_dialog(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    close_web_app = MagicMock()
    stop_local_server = MagicMock()
    monkeypatch.setattr(hooks, "close_web_app", close_web_app)
    monkeypatch.setattr(hooks, "stop_local_server", stop_local_server)
    monkeypatch.setattr(hooks, "_review_time_evaluator", None)

    hooks.cleanup()

    close_web_app.assert_called_once_with()
    stop_local_server.assert_called_once_with()


def test_profile_cleanup_stops_review_time_evaluator(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    did_stop = False

    class FakeReviewTimeEvaluator:
        def stop(self) -> None:
            nonlocal did_stop
            did_stop = True

    monkeypatch.setattr(hooks, "close_web_app", lambda: None)
    monkeypatch.setattr(hooks, "stop_local_server", lambda: None)
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


def test_addon_files_change_stands_smart_notes_down_until_restart(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[str] = []
    monkeypatch.setattr(
        hooks, "ensure_local_server_started", lambda: calls.append("server_start")
    )
    monkeypatch.setattr(hooks, "stop_local_server", lambda: calls.append("server_stop"))
    monkeypatch.setattr(hooks, "cleanup_logger", lambda: calls.append("logger_cleanup"))
    monkeypatch.setattr(hooks.logger, "info", lambda _: None)
    monkeypatch.setattr(hooks, "_addon_files_changing", False)
    monkeypatch.setattr(hooks, "_review_time_evaluator", None)
    monkeypatch.setattr(hooks, "_add_time_evaluator", None)
    processor = cast(NoteProcessor, object())
    on_profile_did_open = hooks.on_profile_did_open(processor)
    on_editor_context = hooks.on_editor_context(processor)
    on_profile_did_open()

    vars(hooks)["_cleanup_before_addon_files_change"]()
    calls.clear()

    # An editor without `.editor` would raise if the hook body ran.
    on_editor_context(SimpleNamespace(), MagicMock())
    on_profile_did_open()

    assert calls == []
    for name in ("_review_time_evaluator", "_add_time_evaluator"):
        assert vars(hooks)[name].is_stopped


def test_cleanup_before_addon_files_change_releases_non_ui_resources(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[str] = []
    monkeypatch.setattr(
        hooks,
        "stop_local_server",
        lambda: calls.append("server_stop"),
    )
    monkeypatch.setattr(hooks.logger, "info", lambda _: None)
    monkeypatch.setattr(hooks, "cleanup_logger", lambda: calls.append("logger_cleanup"))
    monkeypatch.setattr(hooks, "_addon_files_changing", False)

    vars(hooks)["_cleanup_before_addon_files_change"]()

    assert calls.count("server_stop") == 1
    assert calls.count("logger_cleanup") == 1


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


def test_version_stamp_without_write_access_logs_below_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class ReadOnlyConfig:
        last_seen_version = "2.27.0"

        def __setattr__(self, name: str, value: object) -> None:
            raise PermissionError(13, "Permission denied", "meta.json")

    error_logs: list[str] = []
    warning_logs: list[str] = []
    monkeypatch.setattr(hooks, "config", ReadOnlyConfig())
    monkeypatch.setattr(hooks, "get_version", lambda: "2.27.1")
    monkeypatch.setattr(hooks.logger, "error", error_logs.append)
    monkeypatch.setattr(hooks.logger, "warning", warning_logs.append)

    vars(hooks)["_stamp_version_and_show_first_load_window"]()

    assert error_logs == []
    assert len(warning_logs) == 1
