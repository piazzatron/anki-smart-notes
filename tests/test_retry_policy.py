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

from types import TracebackType
from typing import Any, Optional, cast

import aiohttp
import pytest


class RateLimitedResponse:
    status = 429

    async def __aenter__(self):
        return self

    async def __aexit__(
        self,
        exc_type: Optional[type[BaseException]],
        exc_value: Optional[BaseException],
        traceback: Optional[TracebackType],
    ) -> None:
        return None

    def raise_for_status(self) -> None:
        raise aiohttp.ClientResponseError(
            request_info=cast(Any, None),
            history=(),
            status=self.status,
        )


class RateLimitedSession:
    request_count = 0

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        pass

    async def __aenter__(self):
        return self

    async def __aexit__(
        self,
        exc_type: Optional[type[BaseException]],
        exc_value: Optional[BaseException],
        traceback: Optional[TracebackType],
    ) -> None:
        return None

    def get(self, *args: Any, **kwargs: Any) -> RateLimitedResponse:
        self.__class__.request_count += 1
        return RateLimitedResponse()

    def post(self, *args: Any, **kwargs: Any) -> RateLimitedResponse:
        self.__class__.request_count += 1
        return RateLimitedResponse()


@pytest.mark.asyncio
async def test_api_client_gives_up_after_two_rate_limit_retries(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import src.api_client
    from src.api_client import APIClient

    sleeps: list[int] = []
    RateLimitedSession.request_count = 0

    async def sleep(delay: int) -> None:
        sleeps.append(delay)

    monkeypatch.setitem(src.api_client.config.__dict__, "auth_token", "test-token")
    monkeypatch.setattr(src.api_client.aiohttp, "ClientSession", RateLimitedSession)
    monkeypatch.setattr(src.api_client.asyncio, "sleep", sleep)

    with pytest.raises(aiohttp.ClientResponseError) as exc_info:
        await APIClient().get_api_response("generate")

    assert exc_info.value.status == 429
    assert sleeps == [1, 2]
    assert RateLimitedSession.request_count == 3


@pytest.mark.asyncio
async def test_legacy_openai_client_gives_up_after_two_rate_limit_retries(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import src.open_ai_client
    from src.open_ai_client import OpenAIClient

    sleeps: list[int] = []
    RateLimitedSession.request_count = 0

    async def sleep(delay: int) -> None:
        sleeps.append(delay)

    monkeypatch.setattr(
        src.open_ai_client.aiohttp,
        "ClientSession",
        RateLimitedSession,
    )
    monkeypatch.setitem(src.open_ai_client.config.__dict__, "openai_endpoint", "")
    monkeypatch.setitem(
        src.open_ai_client.config.__dict__, "legacy_openai_model", "gpt-4o-mini"
    )
    monkeypatch.setitem(
        src.open_ai_client.config.__dict__, "openai_api_key", "test-key"
    )
    monkeypatch.setattr(src.open_ai_client.asyncio, "sleep", sleep)

    with pytest.raises(aiohttp.ClientResponseError) as exc_info:
        await OpenAIClient().async_get_chat_response("front")

    assert exc_info.value.status == 429
    assert sleeps == [1, 2]
    assert RateLimitedSession.request_count == 3
