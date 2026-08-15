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

import types

import pytest

import src.sentry as sentry_module
from src.api_client import ClientFacingAPIError
from src.sentry import Sentry


class _LegacyAsyncioTimeoutError(Exception):
    pass


@pytest.mark.parametrize(
    ("error", "should_report", "uses_legacy_timeout"),
    [
        (RuntimeError("smart-notes async failure"), True, False),
        (TimeoutError("provider timed out"), False, False),
        (
            ClientFacingAPIError(
                "This request is too long for Google TTS. Please try a different provider."
            ),
            False,
            False,
        ),
        (_LegacyAsyncioTimeoutError("feature flags timed out"), False, True),
    ],
    ids=["unexpected", "timeout", "client-facing", "legacy-timeout"],
)
@pytest.mark.asyncio
async def test_wrap_async_reraises_and_reports_only_unexpected_errors(
    monkeypatch: pytest.MonkeyPatch,
    error: Exception,
    should_report: bool,
    uses_legacy_timeout: bool,
) -> None:
    captured: list[Exception] = []
    shown: list[Exception] = []
    sentry = object.__new__(Sentry)

    if uses_legacy_timeout:
        monkeypatch.setattr(
            sentry_module,
            "asyncio",
            types.SimpleNamespace(TimeoutError=_LegacyAsyncioTimeoutError),
        )
    monkeypatch.setattr(sentry_module, "is_production", lambda: True)
    monkeypatch.setattr(sentry, "capture_exception", lambda e: captured.append(e))
    monkeypatch.setattr(sentry, "_show_error_message", lambda e: shown.append(e))

    async def op() -> None:
        raise error

    with pytest.raises(type(error)) as exc_info:
        await sentry.wrap_async(op)()

    expected_reports = [error] if should_report else []
    assert exc_info.value is error
    assert captured == expected_reports
    assert shown == expected_reports


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
