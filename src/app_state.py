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

from typing import Literal, TypedDict, Union

from .config import config
from .logger import logger
from .sentry import run_async_in_background_with_sentry
from .subscription_provider import (
    PlanInfo,
    SubscriptionState,
    UserStatus,
    subscription_provider,
)
from .ui.state_manager import StateManager


class AppState(TypedDict):
    subscription: Union[SubscriptionState, Literal["Loading"]]
    plan: Union[PlanInfo, None]


class AppStateManager:
    _state: StateManager[AppState]

    def __init__(self) -> None:
        self._state = StateManager[AppState]({"subscription": "Loading", "plan": None})

    def update_subscription_state(self) -> None:
        if not config.auth_token:
            logger.debug("User is not authenticated")
            self._state.update({"subscription": "UNAUTHENTICATED", "plan": None})
            return

        def on_new_status(status: UserStatus) -> None:
            logger.debug(f"Got new subscription status: {status}")
            self._state.update(
                {"subscription": status["subscriptionState"], "plan": status["plan"]}
            )

        run_async_in_background_with_sentry(
            subscription_provider.get_subscription_status, on_new_status
        )


app_state = AppStateManager()
