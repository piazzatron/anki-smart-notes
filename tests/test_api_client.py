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

from typing import Any

import pytest

from src import api_client


class FakeResponse:
    status = 204

    async def __aenter__(self) -> "FakeResponse":
        return self

    async def __aexit__(self, *args: object) -> None:
        return None

    def raise_for_status(self) -> None:
        return None

    async def read(self) -> bytes:
        return b""


class FakeSession:
    def __init__(self) -> None:
        self.calls: list[dict[str, Any]] = []

    async def __aenter__(self) -> "FakeSession":
        return self

    async def __aexit__(self, *args: object) -> None:
        return None

    def post(self, endpoint: str, **kwargs: Any) -> FakeResponse:
        self.calls.append({"endpoint": endpoint, **kwargs})
        return FakeResponse()


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
