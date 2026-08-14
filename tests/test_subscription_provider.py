"""
Copyright (C) 2024 Michael Piazza

This file is part of Smart Notes.

Smart Notes is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

Smart Notes is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with Smart Notes. If not, see <https://www.gnu.org/licenses/>.
"""

from typing import Any
from unittest.mock import AsyncMock

import pytest

from src.subscription_provider import UserInfoProvider


class FakeResponse:
    def __init__(self, payload: dict[str, Any]) -> None:
        self.payload = payload

    async def json(self) -> dict[str, Any]:
        return self.payload


PLAN = {
    "planId": "free",
    "planType": "trial",
    "planName": "Free Trial",
    "notesUsed": 0,
    "notesLimit": 50,
    "daysLeft": 5,
    "textCreditsUsed": 0,
    "textCreditsCapacity": 100,
    "voiceCreditsUsed": 0,
    "voiceCreditsCapacity": 100,
    "imageCreditsUsed": 0,
    "imageCreditsCapacity": 100,
    "totalCreditsUsed": 0,
    "totalCreditsCapacity": 300,
}


@pytest.mark.asyncio
async def test_requires_plan_and_email(monkeypatch: pytest.MonkeyPatch) -> None:
    get_api_response = AsyncMock(return_value=FakeResponse({"plan": None}))
    monkeypatch.setattr(
        "src.subscription_provider.api.get_api_response", get_api_response
    )

    with pytest.raises(RuntimeError, match="required plan"):
        await UserInfoProvider().get_subscription_status()

    get_api_response.return_value = FakeResponse({"plan": PLAN, "email": None})
    with pytest.raises(RuntimeError, match="required email"):
        await UserInfoProvider().get_subscription_status()


@pytest.mark.asyncio
async def test_rejects_internal_plan_identifiers(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    get_api_response = AsyncMock(
        return_value=FakeResponse(
            {"plan": {**PLAN, "planId": "free3"}, "email": "person@example.com"}
        )
    )
    monkeypatch.setattr(
        "src.subscription_provider.api.get_api_response", get_api_response
    )

    with pytest.raises(RuntimeError, match="Unexpected public plan details for trial"):
        await UserInfoProvider().get_subscription_status()


@pytest.mark.asyncio
async def test_accepts_freemium_plan_type(monkeypatch: pytest.MonkeyPatch) -> None:
    freemium_plan = {
        **PLAN,
        "planId": "free_mini_1",
        "planType": "freemium",
        "planName": "Free",
        "notesUsed": None,
        "notesLimit": None,
    }
    monkeypatch.setattr(
        "src.subscription_provider.api.get_api_response",
        AsyncMock(
            return_value=FakeResponse(
                {"plan": freemium_plan, "email": "person@example.com"}
            )
        ),
    )

    status = await UserInfoProvider().get_subscription_status()

    assert status["plan"]["planType"] == "freemium"
