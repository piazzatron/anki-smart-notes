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

from __future__ import annotations

from typing import Any, cast

from anki.cards import CardId
from anki.decks import DeckId

from ...models.smart_fields import (
    ChatGenerationSettings,
    ChatSmartFieldSettings,
    GenerationDefaults,
    ImageGenerationSettings,
    ImagePromptTestRequest,
    ImageSmartFieldSettings,
    SaveTestResultRequest,
    SmartField,
    SmartFieldCreate,
    SmartFieldSettings,
    TextPromptTestRequest,
    TTSGenerationSettings,
    TTSPromptTestRequest,
    TTSSmartFieldSettings,
)
from ...services.assistant_prompt_service import AssistantPrompt
from ...services.assistant_settings_service import AssistantSettings
from ...services.settings_service import Settings
from .models import (
    AssistantGetFieldRequest,
    AssistantHistoryRequest,
    AssistantRecordDto,
    AuthExchangeCodePayload,
    ChatGenerationSettingsDto,
    ChatSmartFieldSettingsDto,
    FeedbackPayload,
    ImageGenerationSettingsDto,
    ImagePromptTestPayload,
    ImageSmartFieldSettingsDto,
    PromptGeneratePayload,
    PromptGenerateRequest,
    SaveTestResultPayload,
    SettingsDto,
    SmartFieldCreatePayload,
    SmartFieldIdPayload,
    SmartFieldUpdatePayload,
    TextPromptTestPayload,
    TTSGenerationSettingsDto,
    TTSPromptTestPayload,
    TTSSmartFieldSettingsDto,
)

# The command endpoints sit behind the local server's session-token boundary, so
# every payload comes from our own webview. We cast each raw dict to its wire
# type and trust it — no runtime revalidation of values we handed the client.
# Missing keys raise KeyError, which the command handler turns into a 400.


def parse_smart_field_create(payload: dict[str, Any]) -> SmartFieldCreate:
    raw = cast(SmartFieldCreatePayload, payload)
    field_type = raw["fieldType"]

    settings: SmartFieldSettings
    if field_type == "chat":
        chat = cast(ChatSmartFieldSettingsDto, raw["settings"])
        settings = ChatSmartFieldSettings(
            prompt_text=chat["promptText"],
            provider=chat["provider"],
            model=chat["model"],
            reasoning_level=chat["reasoningLevel"],
            web_search_enabled=chat["webSearchEnabled"],
            uses_default_generation_settings=chat["usesDefaultGenerationSettings"],
        )
    elif field_type == "tts":
        tts = cast(TTSSmartFieldSettingsDto, raw["settings"])
        settings = TTSSmartFieldSettings(
            source_field_name=tts["sourceFieldName"],
            provider=tts["provider"],
            model=tts["model"],
            voice_id=tts["voiceId"],
            uses_default_generation_settings=tts["usesDefaultGenerationSettings"],
        )
    elif field_type == "image":
        image = cast(ImageSmartFieldSettingsDto, raw["settings"])
        settings = ImageSmartFieldSettings(
            prompt_text=image["promptText"],
            provider=image["provider"],
            model=image["model"],
            uses_default_generation_settings=image["usesDefaultGenerationSettings"],
        )
    else:
        raise ValueError(f"Unknown fieldType: {field_type}")

    return SmartFieldCreate(
        note_type_id=raw["noteTypeId"],
        deck_id=cast(DeckId, raw["deckId"]),
        target_field_name=raw["targetFieldName"],
        enabled=raw["enabled"],
        settings=settings,
    )


def parse_smart_field_update(payload: dict[str, Any]) -> SmartField:
    smart_field = parse_smart_field_create(payload)
    return SmartField(
        id=cast(SmartFieldUpdatePayload, payload)["id"],
        note_type_id=smart_field.note_type_id,
        deck_id=smart_field.deck_id,
        target_field_name=smart_field.target_field_name,
        enabled=smart_field.enabled,
        settings=smart_field.settings,
    )


def parse_smart_field_id(payload: dict[str, Any]) -> str:
    return cast(SmartFieldIdPayload, payload)["id"]


def parse_generation_defaults(payload: dict[str, Any]) -> GenerationDefaults:
    return GenerationDefaults(
        chat=parse_chat_generation_settings(payload["chat"]),
        tts=parse_tts_generation_settings(payload["tts"]),
        image=parse_image_generation_settings(payload["image"]),
    )


def parse_settings(payload: dict[str, Any]) -> Settings:
    raw = cast(SettingsDto, payload)
    return Settings(
        generate_at_review=raw["generateAtReview"],
        regenerate_when_batching=raw["regenerateWhenBatching"],
        debug=raw["debug"],
        language=raw["language"],
        legacy_openai_key=raw["legacyOpenAiKey"],
        legacy_openai_model=raw["legacyOpenAiModel"],
        legacy_openai_host=raw["legacyOpenAiHost"],
        show_wizard_completion=raw["showWizardCompletion"],
        did_dismiss_review_prompt=raw["didDismissReviewPrompt"],
        did_dismiss_discord_prompt=raw["didDismissDiscordPrompt"],
    )


def parse_text_prompt_test(payload: dict[str, Any]) -> TextPromptTestRequest:
    raw = cast(TextPromptTestPayload, payload)
    prompt = raw["prompt"]
    if not prompt.strip():
        raise ValueError("prompt must be a non-empty string")
    return TextPromptTestRequest(
        card_id=_optional_card_id(payload),
        prompt=prompt,
        settings=parse_chat_generation_settings(payload["settings"]),
    )


def parse_image_prompt_test(payload: dict[str, Any]) -> ImagePromptTestRequest:
    raw = cast(ImagePromptTestPayload, payload)
    prompt = raw["prompt"]
    if not prompt.strip():
        raise ValueError("prompt must be a non-empty string")
    return ImagePromptTestRequest(
        card_id=_optional_card_id(payload),
        prompt=prompt,
        settings=parse_image_generation_settings(payload["settings"]),
    )


def parse_tts_prompt_test(payload: dict[str, Any]) -> TTSPromptTestRequest:
    text = cast(TTSPromptTestPayload, payload)["text"]
    if not text.strip():
        raise ValueError("text must be a non-empty string")
    return TTSPromptTestRequest(
        card_id=_optional_card_id(payload),
        text=text,
        settings=parse_tts_generation_settings(payload["settings"]),
    )


def parse_save_test_result(payload: dict[str, Any]) -> SaveTestResultRequest:
    raw = cast(SaveTestResultPayload, payload)
    return SaveTestResultRequest(
        token=raw["token"],
        card_id=_card_id(payload),
        field_name=raw["fieldName"],
    )


def parse_prompt_generate(payload: dict[str, Any]) -> PromptGenerateRequest:
    raw = cast(PromptGeneratePayload, payload)
    field_type = raw["fieldType"]
    if field_type != "chat" and field_type != "image":
        raise ValueError("fieldType must be chat or image")
    return PromptGenerateRequest(
        note_type_id=raw["noteTypeId"],
        deck_id=cast(DeckId, raw["deckId"]),
        target_field_name=raw["targetFieldName"],
        field_type=field_type,
        generation_prompt=raw["generationPrompt"],
    )


def parse_feedback_message(payload: dict[str, Any]) -> str:
    message = cast(FeedbackPayload, payload)["message"].strip()
    if not message:
        raise ValueError("message must be a non-empty string")
    return message


def parse_auth_exchange_code(payload: dict[str, Any]) -> str:
    code = cast(AuthExchangeCodePayload, payload)["code"].strip().upper()
    if not code:
        raise ValueError("Please enter a code.")
    return code


def parse_auth_logout(payload: object) -> None:
    if not isinstance(payload, dict) or payload:
        raise ValueError("auth.logout payload must be an empty object")


def parse_account_refresh(payload: object) -> None:
    if not isinstance(payload, dict) or payload:
        raise ValueError("account.refresh payload must be an empty object")


def parse_ui_open_browser(payload: object) -> None:
    if not isinstance(payload, dict) or payload:
        raise ValueError("ui.openBrowser payload must be an empty object")


def parse_chat_generation_settings(payload: dict[str, Any]) -> ChatGenerationSettings:
    raw = cast(ChatGenerationSettingsDto, payload)
    return ChatGenerationSettings(
        provider=raw["provider"],
        model=raw["model"],
        reasoning_level=raw["reasoningLevel"],
        web_search_enabled=raw["webSearchEnabled"],
    )


def parse_image_generation_settings(payload: dict[str, Any]) -> ImageGenerationSettings:
    raw = cast(ImageGenerationSettingsDto, payload)
    return ImageGenerationSettings(provider=raw["provider"], model=raw["model"])


def parse_tts_generation_settings(payload: dict[str, Any]) -> TTSGenerationSettings:
    raw = cast(TTSGenerationSettingsDto, payload)
    return TTSGenerationSettings(
        provider=raw["provider"],
        model=raw["model"],
        voice_id=raw["voiceId"],
    )


def _card_id(payload: dict[str, Any]) -> CardId:
    return cast(CardId, payload["cardId"])


def _optional_card_id(payload: dict[str, Any]) -> CardId | None:
    card_id = payload.get("cardId")
    return None if card_id is None else cast(CardId, card_id)


def parse_assistant_get_field(payload: dict[str, Any]) -> AssistantGetFieldRequest:
    field_name = payload["fieldName"]
    if not isinstance(field_name, str) or not field_name.strip():
        raise ValueError("fieldName is required")
    return AssistantGetFieldRequest(card_id=_card_id(payload), field_name=field_name)


def parse_assistant_append(payload: dict[str, Any]) -> AssistantRecordDto:
    session_id = payload["sessionId"]
    if not isinstance(session_id, str) or not session_id:
        raise ValueError("sessionId is required")
    message = payload["message"]
    if not isinstance(message, dict):
        raise ValueError("message must be an object")

    return AssistantRecordDto(
        sessionId=session_id,
        cardId=payload.get("cardId"),
        deckId=payload.get("deckId"),
        noteTypeId=payload.get("noteTypeId"),
        seq=0,  # Assigned by the journal, which owns ordering.
        message=message,
    )


def parse_assistant_settings(payload: dict[str, Any]) -> AssistantSettings:
    language = payload["responseLanguage"]
    if not isinstance(language, str) or not language.strip():
        raise ValueError("responseLanguage is required")
    return AssistantSettings(response_language=language)


def parse_assistant_prompts(payload: dict[str, Any]) -> list[AssistantPrompt]:
    prompts = payload["prompts"]
    if not isinstance(prompts, list):
        raise ValueError("prompts must be a list")

    parsed: list[AssistantPrompt] = []
    for prompt in prompts:
        label = prompt.get("label", "")
        text = prompt.get("prompt", "")
        if not isinstance(label, str) or not label.strip():
            raise ValueError("every prompt needs a label")
        if not isinstance(text, str) or not text.strip():
            raise ValueError("every prompt needs prompt text")
        parsed.append(
            AssistantPrompt(id=prompt["id"], label=label.strip(), prompt=text.strip())
        )
    return parsed


def parse_assistant_history(payload: dict[str, Any]) -> AssistantHistoryRequest:
    limit = payload.get("limit", 50)
    if not isinstance(limit, int) or limit <= 0:
        raise ValueError("limit must be a positive integer")
    cursor = payload.get("cursor")
    if cursor is not None and not isinstance(cursor, int):
        raise ValueError("cursor must be an integer")
    return AssistantHistoryRequest(limit=min(limit, 200), cursor=cursor)
