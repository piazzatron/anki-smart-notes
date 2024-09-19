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

from typing import TypedDict, Union

from .config import config
from .constants import (
    APP_LOCKED_ERROR,
    FREE_TRIAL_ENDED_CAPACITY_API_KEY,
    FREE_TRIAL_ENDED_CAPACITY_NO_API_KEY,
    FREE_TRIAL_ENDED_EXPIRED_API_KEY,
    FREE_TRIAL_ENDED_EXPIRED_NO_API_KEY,
    FREE_TRIAL_TEXT_CAPACITY,
    FREE_TRIAL_VOICE_CAPACITY,
    PAID_PLAN_ENDED_CAPACITY_API_KEY,
    PAID_PLAN_ENDED_CAPACITY_NO_API_KEY,
    PAID_PLAN_ENDED_EXPIRED_API_KEY,
    PAID_PLAN_ENDED_EXPIRED_NO_API_KEY,
    PAID_PLAN_TEXT_CAPACITY,
    PAID_PLAN_VOICE_CAPACITY,
)
from .logger import logger
from .sentry import run_async_in_background_with_sentry
from .subscription_provider import (
    PlanInfo,
    SubscriptionState,
    UserStatus,
    subscription_provider,
)
from .ui.state_manager import StateManager
from .ui.ui_utils import show_message_box


class AppState(TypedDict):
    subscription: SubscriptionState
    plan: Union[PlanInfo, None]


class AppStateManager:
    _state: StateManager[AppState]

    def __init__(self) -> None:
        self._state = StateManager[AppState]({"subscription": "LOADING", "plan": None})

    def is_free_trial(self) -> bool:
        return self._state.s["subscription"] in [
            "FREE_TRIAL_ACTIVE",
            "FREE_TRIAL_CAPACITY",
            "FREE_TRIAL_TEXT_CAPACITY",
            "FREE_TRIAL_VOICE_CAPACITY",
            "FREE_TRIAL_EXPIRED",
        ]

    def update_subscription_state(self) -> None:
        if not config.auth_token:
            logger.debug("User is not authenticated")
            self._state.update({"subscription": "UNAUTHENTICATED", "plan": None})
            return

        def on_failure(_) -> None:
            self._state.update({"subscription": "LOADING", "plan": None})

        def on_new_status(status: Union[UserStatus, None]) -> None:
            logger.debug(f"Got new subscription status: {status}")

            if not status:
                on_failure(None)
                return

            old_state = self._state.s.copy()

            new_sub_state = self._make_subscription_state(status["plan"])
            old_sub_state = old_state["subscription"]

            sub_did_end = self._did_subscription_end(old_sub_state, new_sub_state)

            self._state.update({"subscription": new_sub_state, "plan": status["plan"]})

            if sub_did_end:
                self._handle_subscription_did_end(new_sub_state)

        run_async_in_background_with_sentry(
            subscription_provider.get_subscription_status,
            on_new_status,
            on_failure,
            use_collection=False,
        )

    def _make_subscription_state(self, sub: Union[PlanInfo, None]) -> SubscriptionState:
        if not sub:
            return "NO_SUBSCRIPTION"

        is_free = sub["planId"] == "free"
        text_capacity_reached = sub["textCreditsUsed"] >= sub["textCreditsCapacity"]
        voice_capacity_reached = sub["voiceCreditsUsed"] >= sub["voiceCreditsCapacity"]

        if (
            is_free
            and sub["notesLimit"]
            and sub["notesUsed"]
            and sub["notesUsed"] >= sub["notesLimit"]
        ):
            return "FREE_TRIAL_CAPACITY"

        if sub["daysLeft"] <= 0:
            return "FREE_TRIAL_EXPIRED" if is_free else "PAID_PLAN_EXPIRED"

        if text_capacity_reached and voice_capacity_reached:
            return "FREE_TRIAL_CAPACITY" if is_free else "PAID_PLAN_CAPACITY"

        if text_capacity_reached:
            return "FREE_TRIAL_TEXT_CAPACITY" if is_free else "PAID_PLAN_TEXT_CAPACITY"

        if voice_capacity_reached:
            return (
                "FREE_TRIAL_VOICE_CAPACITY" if is_free else "PAID_PLAN_VOICE_CAPACITY"
            )

        return "FREE_TRIAL_ACTIVE" if is_free else "PAID_PLAN_ACTIVE"

    def _did_subscription_end(
        self, old_state: SubscriptionState, new_state: SubscriptionState
    ) -> bool:
        did_end = old_state in [
            "PAID_PLAN_ACTIVE",
            "FREE_TRIAL_ACTIVE",
        ] and new_state in [
            "UNAUTHENTICATED",
            "NO_SUBSCRIPTION",
            "FREE_TRIAL_EXPIRED",
            "FREE_TRIAL_CAPACITY",
            "FREE_TRIAL_TEXT_CAPACITY",
            "FREE_TRIAL_VOICE_CAPACITY",
            "PAID_PLAN_EXPIRED",
            "PAID_PLAN_CAPACITY",
            "PAID_PLAN_TEXT_CAPACITY",
            "PAID_PLAN_VOICE_CAPACITY",
        ]
        if did_end:
            logger.debug(
                f"Subscription did end, transitioned from {old_state} to {new_state}"
            )
        return bool(did_end)

    def _handle_subscription_did_end(self, new_sub: SubscriptionState) -> None:
        plan_type = "trial" if "FREE" in new_sub else "paid"
        end_type = (
            "capacity"
            if new_sub in ["FREE_TRIAL_CAPACITY", "PAID_PLAN_CAPACITY"]
            else (
                "text"
                if new_sub in ["FREE_TRIAL_TEXT_CAPACITY", "PAID_PLAN_TEXT_CAPACITY"]
                else (
                    "voice"
                    if new_sub
                    in ["FREE_TRIAL_VOICE_CAPACITY", "PAID_PLAN_VOICE_CAPACITY"]
                    else "expired"
                )
            )
        )
        is_api_key = "api_key" if has_api_key() else "no_api_key"

        error_map = {
            "trial": {
                "capacity": {
                    "api_key": FREE_TRIAL_ENDED_CAPACITY_API_KEY,
                    "no_api_key": FREE_TRIAL_ENDED_CAPACITY_NO_API_KEY,
                },
                "expired": {
                    "api_key": FREE_TRIAL_ENDED_EXPIRED_API_KEY,
                    "no_api_key": FREE_TRIAL_ENDED_EXPIRED_NO_API_KEY,
                },
                "text": {
                    "api_key": FREE_TRIAL_TEXT_CAPACITY,
                    "no_api_key": FREE_TRIAL_TEXT_CAPACITY,
                },
                "voice": {
                    "api_key": FREE_TRIAL_VOICE_CAPACITY,
                    "no_api_key": FREE_TRIAL_VOICE_CAPACITY,
                },
            },
            "paid": {
                "capacity": {
                    "api_key": PAID_PLAN_ENDED_CAPACITY_API_KEY,
                    "no_api_key": PAID_PLAN_ENDED_CAPACITY_NO_API_KEY,
                },
                "expired": {
                    "api_key": PAID_PLAN_ENDED_EXPIRED_API_KEY,
                    "no_api_key": PAID_PLAN_ENDED_EXPIRED_NO_API_KEY,
                },
                "text": {
                    "api_key": PAID_PLAN_TEXT_CAPACITY,
                    "no_api_key": PAID_PLAN_TEXT_CAPACITY,
                },
                "voice": {
                    "api_key": PAID_PLAN_VOICE_CAPACITY,
                    "no_api_key": PAID_PLAN_VOICE_CAPACITY,
                },
            },
        }

        error_message = (
            error_map.get(plan_type, {}).get(end_type, {}).get(is_api_key, None)
        )

        # Migrate you from anthropic to OpenAI if necessary
        if config.chat_provider == "anthropic":
            logger.debug("Migrating ot OpenAI chat provider")
            config.chat_provider = "openai"
            config.chat_model = "gpt-4o"

        if not error_message:
            logger.error(
                f"Unexpectedly couldnt find error for {plan_type}, {end_type}, {is_api_key}"
            )
            return
        else:
            show_message_box(error_message)


app_state = AppStateManager()

# Mode selection stuff


def is_app_unlocked(show_box=False) -> bool:
    state = app_state._state.s["subscription"]
    unlocked = state in [
        "FREE_TRIAL_ACTIVE",
        "PAID_PLAN_ACTIVE",
        "FREE_TRIAL_TEXT_CAPACITY",
        "FREE_TRIAL_VOICE_CAPACITY",
        "PAID_PLAN_TEXT_CAPACITY",
        "PAID_PLAN_VOICE_CAPACITY",
    ]
    if not unlocked and show_box:
        show_message_box(APP_LOCKED_ERROR)
    return unlocked


def is_at_text_capacity() -> bool:
    return app_state._state.s["subscription"] in [
        "FREE_TRIAL_TEXT_CAPACITY",
        "PAID_PLAN_TEXT_CAPACITY",
    ]


def is_at_voice_capacity() -> bool:
    return app_state._state.s["subscription"] in [
        "FREE_TRIAL_VOICE_CAPACITY",
        "PAID_PLAN_VOICE_CAPACITY",
    ]


def has_api_key() -> bool:
    return bool(config.openai_api_key)


def is_app_legacy() -> bool:
    return not is_app_unlocked() and has_api_key()


def is_app_unlocked_or_legacy(show_box=False) -> bool:
    allowed = is_app_unlocked() or has_api_key()
    if not allowed and show_box:
        show_message_box(APP_LOCKED_ERROR)
    return allowed
