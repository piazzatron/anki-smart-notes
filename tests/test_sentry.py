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

import json
import types
from uuid import uuid4

import aiohttp
import pytest

import src.sentry as sentry_module
from src.api_client import UserDisplayableError
from src.sentry import Sentry
from tests.fixtures import RecordingSentryTransport


@pytest.mark.parametrize("capture_method", ["logging", "direct"])
def test_captured_exceptions_keep_stack_without_local_credentials(
    monkeypatch: pytest.MonkeyPatch, capture_method: str
) -> None:
    transport = RecordingSentryTransport()
    monkeypatch.setattr("sentry_sdk.client.make_transport", lambda _: transport)
    monkeypatch.setattr(sentry_module, "is_production", lambda: True)
    sentry = Sentry("https://public@example.invalid/1", "test", "production")
    jwt = uuid4().hex

    with sentry.hub:
        try:
            raise RuntimeError("smart-notes synthetic failure")
        except RuntimeError as error:
            if capture_method == "logging":
                sentry_module.logger.exception("Synthetic command failed")
            else:
                sentry.capture_exception(error)

    assert sentry.hub.client is not None
    sentry.hub.client.close()

    assert len(transport.events) == 1
    event = transport.events[0]
    assert "exception" in event
    frames = event["exception"]["values"][0]["stacktrace"]["frames"]
    assert frames
    assert all(not frame.get("vars") for frame in frames)
    assert jwt not in json.dumps(event)


class _LegacyAsyncioTimeoutError(Exception):
    pass


@pytest.mark.parametrize(
    ("error", "should_report", "uses_legacy_timeout"),
    [
        (RuntimeError("smart-notes async failure"), True, False),
        (TimeoutError("provider timed out"), False, False),
        (aiohttp.ClientConnectionError("offline"), False, False),
        (
            UserDisplayableError(
                "This request is too long for Google TTS. Please try a different provider.",
                status=413,
            ),
            False,
            False,
        ),
        (_LegacyAsyncioTimeoutError("feature flags timed out"), False, True),
    ],
    ids=[
        "unexpected",
        "timeout",
        "offline",
        "user-displayable",
        "legacy-timeout",
    ],
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
