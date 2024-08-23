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

from typing import Literal, TypedDict

from .api_client import api

SubscriptionState = Literal[
    "UNAUTHENTICATED",  # This is not returned, jic there's no JWT
    "NO_SUBSCRIPTION",
    "FREE_TRIAL_ACTIVE",
    "FREE_TRIAL_EXPIRED",
    "FREE_TRIAL_CAPACITY",
    "PAID_PLAN_ACTIVE",
    "PAID_PLAN_EXPIRED",
    "PAID_PLAN_CAPACITY",
]


# TODO: awfully named lol
class SubscriptionStatus(TypedDict):
    subscriptionState: SubscriptionState


class SubscriptionProvider:
    async def get_subscription_status(self) -> SubscriptionStatus:
        print("makin req")
        response = await api.get_api_response(
            path="user",
            method="GET",
        )
        print(response)
        status: SubscriptionStatus = await response.json()
        print(status)

        return status


subscription_provider = SubscriptionProvider()