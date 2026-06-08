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
from typing import cast

import pytest

import src.hooks as hooks
from src.note_proccessor import NoteProcessor


def test_profile_did_open_restarts_local_server_after_profile_switch(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[str] = []

    class FakeLocalServer:
        def __init__(self, processor: object) -> None:
            calls.append("server_init")

        def start(self) -> None:
            calls.append("server_start")

    monkeypatch.setattr(hooks, "_local_server", None)
    monkeypatch.setitem(
        sys.modules,
        "src.local_server",
        SimpleNamespace(LocalServer=FakeLocalServer),
    )

    processor = cast(NoteProcessor, object())
    hooks.on_profile_did_open(processor)()
    hooks.on_profile_did_open(processor)()

    assert calls == [
        "server_init",
        "server_start",
    ]


def test_profile_did_open_hook_is_registered() -> None:
    assert hasattr(hooks.gui_hooks, "profile_did_open")
