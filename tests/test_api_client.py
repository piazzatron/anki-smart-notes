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

import asyncio
from typing import Any, Optional, cast

import aiohttp
import pytest

from src import api_client


class FakeResponse:
    def __init__(self, status: int = 204) -> None:
        self.status = status
        self.json_body: dict[str, object] = {}

    async def __aenter__(self) -> "FakeResponse":
        return self

    async def __aexit__(self, *args: object) -> None:
        return None

    def raise_for_status(self) -> None:
        if self.status >= 400:
            raise aiohttp.ClientResponseError(
                request_info=cast(aiohttp.RequestInfo, None),
                history=(),
                status=self.status,
                message="request failed",
            )
        return None

    async def read(self) -> bytes:
        return b""

    async def json(self) -> dict[str, object]:
        return self.json_body


class FakeSession:
    response_status = 204
    response_json: dict[str, object] = {}
    request_error: Optional[Exception] = None

    def __init__(self) -> None:
        self.calls: list[dict[str, Any]] = []

    async def __aenter__(self) -> "FakeSession":
        return self

    async def __aexit__(self, *args: object) -> None:
        return None

    def post(self, endpoint: str, **kwargs: Any) -> FakeResponse:
        self.calls.append({"endpoint": endpoint, **kwargs})
        if self.request_error:
            raise self.request_error
        response = FakeResponse(self.response_status)
        response.json_body = self.response_json
        return response


@pytest.mark.asyncio
async def test_api_requests_include_plugin_version(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake_session = FakeSession()
    monkeypatch.setattr(api_client.aiohttp, "ClientSession", lambda: fake_session)
    monkeypatch.setattr(
        api_client, "config", type("Config", (), {"auth_token": "test-token"})()
    )
    monkeypatch.setattr(api_client, "get_server_url", lambda: "https://server.test")
    monkeypatch.setattr(api_client, "get_version", lambda: "1.2.3")

    await api_client.APIClient().get_api_response("events", {"event": "test_event"})

    assert fake_session.calls[0]["endpoint"] == "https://server.test/api/events"
    assert fake_session.calls[0]["headers"] == {
        "Authorization": "Bearer test-token",
        "Content-Type": "application/json",
        "x-sn-plugin-version": "1.2.3",
        "x-sn-source": "anki-plugin",
    }
    assert fake_session.calls[0]["json"] == {"event": "test_event"}


@pytest.mark.asyncio
async def test_api_client_does_not_retry_server_rate_limits(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake_session = FakeSession()
    fake_session.response_status = 429
    monkeypatch.setattr(api_client.aiohttp, "ClientSession", lambda: fake_session)
    monkeypatch.setattr(
        api_client, "config", type("Config", (), {"auth_token": "test-token"})()
    )
    monkeypatch.setattr(api_client, "get_server_url", lambda: "https://server.test")
    monkeypatch.setattr(api_client, "get_version", lambda: "1.2.3")

    with pytest.raises(aiohttp.ClientResponseError):
        await api_client.APIClient().get_api_response("chat", {"message": "hello"})

    assert len(fake_session.calls) == 1


@pytest.mark.asyncio
async def test_api_client_raises_client_facing_message_for_server_message(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    message = (
        "This request is too long for Google TTS. Please try a different provider."
    )
    fake_session = FakeSession()
    fake_session.response_status = 413
    fake_session.response_json = {"message": message}
    monkeypatch.setattr(api_client.aiohttp, "ClientSession", lambda: fake_session)
    monkeypatch.setattr(
        api_client, "config", type("Config", (), {"auth_token": "test-token"})()
    )
    monkeypatch.setattr(api_client, "get_server_url", lambda: "https://server.test")
    monkeypatch.setattr(api_client, "get_version", lambda: "1.2.3")

    with pytest.raises(api_client.ClientFacingAPIError, match=message):
        await api_client.APIClient().get_api_response("tts", {"message": "hello"})

    assert len(fake_session.calls) == 1


@pytest.mark.asyncio
async def test_api_client_raises_client_facing_message_for_server_error_field(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake_session = FakeSession()
    fake_session.response_status = 500
    fake_session.response_json = {"error": "The provider rejected this request."}
    monkeypatch.setattr(api_client.aiohttp, "ClientSession", lambda: fake_session)
    monkeypatch.setattr(
        api_client, "config", type("Config", (), {"auth_token": "test-token"})()
    )
    monkeypatch.setattr(api_client, "get_server_url", lambda: "https://server.test")
    monkeypatch.setattr(api_client, "get_version", lambda: "1.2.3")

    with pytest.raises(
        api_client.ClientFacingAPIError,
        match="The provider rejected this request.",
    ):
        await api_client.APIClient().get_api_response("tts", {"message": "hello"})

    assert len(fake_session.calls) == 1


@pytest.mark.asyncio
async def test_api_client_raises_client_facing_message_for_validation_errors(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake_session = FakeSession()
    fake_session.response_status = 400
    fake_session.response_json = {"error": "Provider is required"}
    monkeypatch.setattr(api_client.aiohttp, "ClientSession", lambda: fake_session)
    monkeypatch.setattr(
        api_client, "config", type("Config", (), {"auth_token": "test-token"})()
    )
    monkeypatch.setattr(api_client, "get_server_url", lambda: "https://server.test")
    monkeypatch.setattr(api_client, "get_version", lambda: "1.2.3")

    with pytest.raises(api_client.ClientFacingAPIError, match="Provider is required"):
        await api_client.APIClient().get_api_response("tts", {"message": "hello"})

    assert len(fake_session.calls) == 1


@pytest.mark.asyncio
async def test_api_client_does_not_retry_timeouts(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake_session = FakeSession()
    fake_session.request_error = asyncio.TimeoutError()
    monkeypatch.setattr(api_client.aiohttp, "ClientSession", lambda: fake_session)
    monkeypatch.setattr(
        api_client, "config", type("Config", (), {"auth_token": "test-token"})()
    )
    monkeypatch.setattr(api_client, "get_server_url", lambda: "https://server.test")
    monkeypatch.setattr(api_client, "get_version", lambda: "1.2.3")

    with pytest.raises(asyncio.TimeoutError):
        await api_client.APIClient().get_api_response("chat", {"message": "hello"})

    assert len(fake_session.calls) == 1
