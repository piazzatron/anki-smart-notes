# type: ignore

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
import types

import aiohttp
import pytest

import src.app_state
from src.app_state import AppStateManager


@pytest.mark.parametrize(
    ("error", "is_expected"),
    [
        (TimeoutError(), True),
        (
            aiohttp.ClientOSError(10054, "connection forcibly closed by remote host"),
            True,
        ),
        (RuntimeError("unexpected"), False),
    ],
)
def test_account_refresh_logs_network_failures_below_error(
    monkeypatch, error, is_expected
):
    error_logs = []
    info_logs = []

    def fail_refresh(op, on_success, on_failure, **kwargs):
        on_failure(error)

    monkeypatch.setattr(
        src.app_state, "config", types.SimpleNamespace(auth_token="token")
    )
    monkeypatch.setattr(
        src.app_state, "run_async_in_background_with_sentry", fail_refresh
    )
    monkeypatch.setattr(src.app_state.logger, "error", error_logs.append)
    monkeypatch.setattr(src.app_state.logger, "info", info_logs.append)

    AppStateManager().update_account_state()

    assert len(error_logs) == (0 if is_expected else 1)
    assert len(info_logs) == (1 if is_expected else 0)


def test_retry_failed_refresh_recovers_from_a_failed_startup_refresh(monkeypatch):
    now = [1000.0]
    responses = [TimeoutError(), {"plan": {"planType": "paid"}, "email": "a@b.c"}]
    requests = []

    async def get_user_status():
        requests.append(now[0])
        response = responses.pop(0)
        if isinstance(response, Exception):
            raise response
        return response

    # Run the refresh synchronously; only the server call is faked.
    def run_now(op, on_success, on_failure, **kwargs):
        try:
            result = asyncio.run(op())
        except Exception as e:
            on_failure(e)
            return
        on_success(result)

    monkeypatch.setattr(
        src.app_state, "config", types.SimpleNamespace(auth_token="token")
    )
    monkeypatch.setattr(src.app_state, "run_async_in_background_with_sentry", run_now)
    monkeypatch.setattr(
        src.app_state.subscription_provider, "get_user_status", get_user_status
    )
    monkeypatch.setattr(
        src.app_state, "time", types.SimpleNamespace(monotonic=lambda: now[0])
    )
    manager = AppStateManager()

    # The startup refresh times out, leaving the account LOADING.
    manager.update_account_state()
    assert manager.state["status"] == "LOADING"

    # Generation retries, but not within a minute of the last attempt.
    manager.retry_failed_refresh()
    assert len(requests) == 1

    now[0] += src.app_state.REFRESH_RETRY_SECONDS
    manager.retry_failed_refresh()
    assert len(requests) == 2
    assert manager.state["status"] == "AUTHENTICATED"

    # Once the account is confirmed, generation never retries.
    now[0] += src.app_state.REFRESH_RETRY_SECONDS
    manager.retry_failed_refresh()
    assert len(requests) == 2
