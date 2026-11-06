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

from collections.abc import Awaitable, Callable
from typing import Any

import pytest
from fixtures import MockAppState

from src.api_client import UserDisplayableError
from src.ui import custom_prompt
from src.ui.custom_prompt import CustomImagePrompt, CustomTTSPrompt


def test_custom_image_prompt_shows_user_displayable_errors_directly(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    shown_messages: list[str] = []
    ui_updates = 0

    def fake_run_async(
        _fn: Callable[[], Awaitable[Any]],
        _on_success: Callable[[Any], None],
        on_error: Callable[[Exception], None],
    ) -> None:
        on_error(
            UserDisplayableError(
                "The image provider rejected this prompt due to sensitive content. Try rewording it or using a different image prompt.",
                status=400,
            )
        )

    class FakePromptWindow:
        def toPlainText(self) -> str:
            return "draw this"

    class FakeState:
        s = {"image_model": "gpt-image-2-low", "image_provider": "openai"}

    class FakeImageOptions:
        state = FakeState()

    def update_ui_states() -> None:
        nonlocal ui_updates
        ui_updates += 1

    prompt: Any = CustomImagePrompt.__new__(CustomImagePrompt)
    prompt._prompt_window = FakePromptWindow()
    prompt._note = object()
    prompt._deck_id = 1
    prompt._loading = True
    prompt.image_options = FakeImageOptions()
    prompt._update_ui_states = update_ui_states

    monkeypatch.setattr(
        custom_prompt, "run_async_in_background_with_sentry", fake_run_async
    )
    monkeypatch.setattr(custom_prompt, "show_message_box", shown_messages.append)

    CustomImagePrompt.on_generate(prompt)

    assert shown_messages == [
        "The image provider rejected this prompt due to sensitive content. Try rewording it or using a different image prompt."
    ]
    assert prompt._loading is False
    assert ui_updates == 1


@pytest.mark.parametrize(
    ("plan_type", "provider", "model", "voice_id", "user_closes", "outcome"),
    [
        ("free", "google", "standard", "ja-JP-Standard-A", True, "generates"),
        ("free", "google", "neural", "ja-JP-Neural2-B", True, "upgrades"),
        ("free", "voicevox", "voicevox", "3", True, "upgrades"),
        # Cancelling "Close and lose results?" keeps the dialog, usable, and no sheet.
        ("free", "google", "neural", "ja-JP-Neural2-B", False, "stays"),
        ("medium", "voicevox", "voicevox", "3", True, "generates"),
    ],
)
def test_custom_tts_offers_upgrade_for_voices_the_plan_lacks(
    monkeypatch: pytest.MonkeyPatch,
    plan_type: str,
    provider: str,
    model: str,
    voice_id: str,
    user_closes: bool,
    outcome: str,
) -> None:
    import src.app_state

    started: list[Any] = []
    opened: list[dict[str, Any]] = []
    closed: list[bool] = []

    class FakePromptWindow:
        def toPlainText(self) -> str:
            return "{{Front}}"

    class FakeState:
        s = {"tts_provider": provider, "tts_model": model, "tts_voice": voice_id}

    class FakeTTSOptions:
        state = FakeState()

    prompt: Any = CustomTTSPrompt.__new__(CustomTTSPrompt)
    prompt._prompt_window = FakePromptWindow()
    prompt._note = object()
    prompt._loading = True
    prompt.tts_options = FakeTTSOptions()
    prompt._update_ui_states = lambda: None
    prompt.reject = lambda: closed.append(user_closes)
    prompt.isVisible = lambda: not any(closed)

    monkeypatch.setattr(src.app_state, "app_state", MockAppState(plan_type))
    monkeypatch.setattr(
        custom_prompt,
        "run_async_in_background_with_sentry",
        lambda *args, **kwargs: started.append(args),
    )
    monkeypatch.setattr(
        custom_prompt, "open_web_app", lambda **kwargs: opened.append(kwargs)
    )

    CustomTTSPrompt.on_generate(prompt)

    if outcome == "generates":
        assert (len(started), opened) == (1, [])
    else:
        assert started == []
        assert prompt._loading is False
        assert opened == (
            [{"upgrade_feature": "voice"}] if outcome == "upgrades" else []
        )
