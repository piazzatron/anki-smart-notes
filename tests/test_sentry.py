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

import pytest

import src.sentry as sentry_module


def test_should_send_event_filters_non_smart_notes_logs(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(sentry_module, "is_production", lambda: True)

    assert not sentry_module._should_send_event({"logger": "hypertts"})


def test_should_send_event_keeps_smart_notes_logs(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(sentry_module, "is_production", lambda: True)

    assert sentry_module._should_send_event(
        {"logger": "smart_notes", "message": "Smart Notes failed"}
    )


def test_should_send_event_filters_loggerless_third_party_exception(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(sentry_module, "is_production", lambda: True)

    assert not sentry_module._should_send_event(
        {
            "logger": "",
            "exception": {
                "values": [
                    {
                        "type": "ServicePermissionError",
                        "value": "Billing must be enabled",
                        "stacktrace": {
                            "frames": [
                                {
                                    "filename": "hypertts_addon\\services\\service_google.py",
                                    "module": "hypertts_addon.services.service_google",
                                }
                            ]
                        },
                    }
                ]
            },
        }
    )


def test_should_send_event_keeps_loggerless_smart_notes_exception_by_module(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(sentry_module, "is_production", lambda: True)

    assert sentry_module._should_send_event(
        {
            "exception": {
                "values": [
                    {
                        "type": "RuntimeError",
                        "value": "Generation failed",
                        "stacktrace": {
                            "frames": [
                                {
                                    "filename": "src\\note_proccessor.py",
                                    "module": "src.note_proccessor",
                                }
                            ]
                        },
                    }
                ]
            },
        }
    )


def test_should_send_event_keeps_loggerless_smart_notes_exception_by_addon_path(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(sentry_module, "is_production", lambda: True)

    assert sentry_module._should_send_event(
        {
            "exception": {
                "values": [
                    {
                        "type": "RuntimeError",
                        "value": "Generation failed",
                        "stacktrace": {
                            "frames": [
                                {
                                    "filename": "1531888719\\src\\note_proccessor.py",
                                    "module": "__main__",
                                }
                            ]
                        },
                    }
                ]
            },
        }
    )


def test_should_send_event_keeps_loggerless_smart_notes_exception_by_value(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(sentry_module, "is_production", lambda: True)

    assert sentry_module._should_send_event(
        {
            "exception": {
                "values": [
                    {
                        "type": "RuntimeError",
                        "value": "smart-notes failed before stack capture",
                    }
                ]
            },
        }
    )
