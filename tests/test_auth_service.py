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

from typing import Any, Optional

import pytest

from src.services import auth_service


class FakeResponse:
    def __init__(self, status: int, body: object) -> None:
        self.status = status
        self.body = body

    async def __aenter__(self) -> "FakeResponse":
        return self

    async def __aexit__(
        self,
        exc_type: Optional[type[BaseException]],
        exc: Optional[BaseException],
        traceback: object,
    ) -> None:
        return None

    async def json(self) -> object:
        return self.body


class FakeSession:
    def __init__(self, response: FakeResponse) -> None:
        self.response = response
        self.post_args: Optional[tuple[str, dict[str, Any]]] = None

    async def __aenter__(self) -> "FakeSession":
        return self

    async def __aexit__(
        self,
        exc_type: Optional[type[BaseException]],
        exc: Optional[BaseException],
        traceback: object,
    ) -> None:
        return None

    def post(self, url: str, **kwargs: Any) -> FakeResponse:
        self.post_args = (url, kwargs)
        return self.response


@pytest.mark.asyncio
async def test_exchange_auth_code_returns_token(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    session = FakeSession(FakeResponse(200, {"jwt": "abc.def.ghi"}))
    monkeypatch.setattr(
        auth_service.aiohttp,
        "ClientSession",
        lambda **_: session,
    )
    monkeypatch.setattr(auth_service, "get_server_url", lambda: "https://server.test")

    assert await auth_service.exchange_auth_code("ABC123") == "abc.def.ghi"
    assert session.post_args == (
        "https://server.test/auth/code/exchange",
        {
            "json": {"code": "ABC123"},
            "headers": {"x-sn-source": "anki-plugin"},
        },
    )


@pytest.mark.asyncio
async def test_exchange_auth_code_maps_rejected_code(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    session = FakeSession(FakeResponse(400, {"error": "INVALID_OR_EXPIRED"}))
    monkeypatch.setattr(
        auth_service.aiohttp,
        "ClientSession",
        lambda **_: session,
    )

    with pytest.raises(ValueError, match="invalid or has expired"):
        await auth_service.exchange_auth_code("BADCODE")
