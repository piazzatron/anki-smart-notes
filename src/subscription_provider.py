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

from typing import Literal, Optional, TypedDict, Union

from .api_client import api
from .config import config

SubscriptionState = Literal[
    "LOADING",
    "UNAUTHENTICATED",  # This is not returned, jic there's no JWT
    "NO_SUBSCRIPTION",
    "FREE_TRIAL_ACTIVE",
    "FREE_TRIAL_EXPIRED",
    "FREE_TRIAL_CAPACITY",
    "PAID_PLAN_ACTIVE",
    "PAID_PLAN_EXPIRED",
    "PAID_PLAN_CAPACITY",
]


class PlanInfo(TypedDict):
    planId: Union[Literal["free"], str]
    planName: str
    notesUsed: Optional[int]
    notesLimit: Optional[int]
    daysLeft: int
    textCreditsUsed: int
    textCreditsCapacity: int
    voiceCreditsUsed: int
    voiceCreditsCapacity: int
    imageCreditsUsed: int
    imageCreditsCapacity: int
    totalCreditsUsed: int
    totalCreditsCapacity: int


class UserStatus(TypedDict):
    plan: Optional[PlanInfo]
    error: Optional[str]


class UserInfoProvider:
    async def get_subscription_status(self) -> UserStatus:
        response = await api.get_api_response(
            path=f"user?uuid={config.uuid}",
            method="GET",
        )
        status: UserStatus = await response.json()

        return status


subscription_provider = UserInfoProvider()
