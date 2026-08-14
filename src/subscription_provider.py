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

from typing import Any, Literal, Optional, TypedDict, cast

from .api_client import api

SubscriptionState = Literal[
    "LOADING",
    "UNAUTHENTICATED",  # This is not returned, jic there's no JWT
    "FREE_TRIAL_ACTIVE",
    "FREE_TRIAL_EXPIRED",
    "FREE_TRIAL_CAPACITY",
    "PAID_PLAN_ACTIVE",
    "PAID_PLAN_EXPIRED",
    "PAID_PLAN_CAPACITY",
]


LegacyPlanId = Literal["free", "free_mini_1", "small1", "medium1", "large1"]
PlanType = Literal["trial", "freemium", "small", "medium", "large"]
PlanName = Literal["Free Trial", "Free", "Lite", "Standard", "Pro"]

PUBLIC_PLAN_DETAILS: dict[PlanType, tuple[LegacyPlanId, PlanName]] = {
    "trial": ("free", "Free Trial"),
    "freemium": ("free_mini_1", "Free"),
    "small": ("small1", "Lite"),
    "medium": ("medium1", "Standard"),
    "large": ("large1", "Pro"),
}


class PlanInfo(TypedDict):
    # Deprecated server field retained for compatibility with older clients.
    planId: LegacyPlanId
    planType: PlanType
    planName: PlanName
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
    plan: PlanInfo
    email: str


class UserInfoProvider:
    async def get_subscription_status(self) -> UserStatus:
        response = await api.get_api_response(
            path="user",
            method="GET",
        )
        status: dict[str, Any] = await response.json()
        if status.get("error"):
            raise RuntimeError(f"User status request failed: {status['error']}")

        plan = status.get("plan")
        if not isinstance(plan, dict):
            raise RuntimeError("Authenticated user status is missing its required plan")

        email = status.get("email")
        if not isinstance(email, str) or not email:
            raise RuntimeError(
                "Authenticated user status is missing its required email"
            )

        plan_type = plan.get("planType")
        plan_id = plan.get("planId")
        plan_name = plan.get("planName")
        if plan_type not in PUBLIC_PLAN_DETAILS:
            raise RuntimeError(f"Unexpected public plan type: {plan_type}")
        if (plan_id, plan_name) != PUBLIC_PLAN_DETAILS[plan_type]:
            raise RuntimeError(
                f"Unexpected public plan details for {plan_type}: "
                f"{plan_id}, {plan_name}"
            )

        return {"plan": cast(PlanInfo, plan), "email": email}


subscription_provider = UserInfoProvider()
