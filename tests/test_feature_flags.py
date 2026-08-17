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

from collections.abc import Callable
from unittest.mock import Mock

import pytest

from src import feature_flags
from src.event_bus import StateInvalidated


def test_refresh_feature_flags_republishes_web_state(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    publish = Mock()
    monkeypatch.setattr(feature_flags.flags, "review_free_month", False)
    monkeypatch.setattr(feature_flags.event_bus, "publish", publish)

    def complete_request(
        _operation: object,
        on_success: Callable[[feature_flags.FeatureFlagsPayload], None],
        _on_failure: object,
        **_kwargs: object,
    ) -> None:
        on_success({"review_free_month": True})

    monkeypatch.setattr(
        feature_flags,
        "run_async_in_background_with_sentry",
        complete_request,
    )

    feature_flags.refresh_feature_flags()

    assert feature_flags.flags.review_free_month is True
    assert isinstance(publish.call_args.args[0], StateInvalidated)
