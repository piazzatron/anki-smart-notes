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
import concurrent.futures
import threading
import traceback
from collections.abc import Mapping
from typing import Any, Optional, TypedDict, cast

from aiohttp import web
from anki.decks import DeckId
from anki.notes import NoteId
from aqt import mw
from aqt.qt import QDialog

from .app_state import app_state
from .config import config
from .constants import GLOBAL_DECK_ID, SITE_URL_DEV, SITE_URL_PROD
from .logger import logger
from .models import (
    ChatModels,
    ChatProviders,
    FieldExtras,
    ImageModels,
    ImageProviders,
    OverridableChatOptionsDict,
    OverridableImageOptionsDict,
    OverrideableTTSOptionsDict,
    SmartFieldType,
    TTSModels,
    TTSProviders,
)
from .note_proccessor import NoteProcessor
from .notes import get_fields
from .prompts import (
    add_or_update_prompts,
    get_extras,
    get_prompts_for_note,
    remove_prompt,
)
from .sentry import sentry
from .ui.prompt_dialog import PromptDialog

# -- Request param types --


class GetSmartFieldsParams(TypedDict, total=False):
    noteType: str  # required
    deckId: int


class ChatOptionsParams(TypedDict, total=False):
    provider: ChatProviders
    model: ChatModels
    temperature: int
    markdownToHtml: bool
    webSearch: bool


class TTSOptionsParams(TypedDict, total=False):
    provider: TTSProviders
    model: TTSModels
    voice: str
    stripHtml: bool


class ImageOptionsParams(TypedDict, total=False):
    provider: ImageProviders
    model: ImageModels


class SmartFieldParams(TypedDict, total=False):
    noteType: str  # required
    field: str  # required
    prompt: str  # required
    type: SmartFieldType
    deckId: int
    automatic: bool
    useCustomModel: bool
    chatOptions: ChatOptionsParams
    ttsOptions: TTSOptionsParams
    imageOptions: ImageOptionsParams


class RemoveSmartFieldParams(TypedDict, total=False):
    noteType: str  # required
    field: str  # required
    deckId: int


class GenerateNoteParams(TypedDict, total=False):
    noteId: int  # required
    deckId: int
    overwrite: bool
    targetField: str


class GenerateNotesParams(TypedDict, total=False):
    noteIds: list[int]  # required
    deckId: int
    overwrite: bool


# -- Response types --


class SmartFieldInfo(TypedDict):
    prompt: str
    extras: Optional[FieldExtras]


class GenerateNoteResult(TypedDict):
    updated: bool
    fields: dict[str, str]


class GenerateNotesResult(TypedDict):
    updated: list[int]
    failed: list[int]
    skipped: list[int]


class ApiResponse(TypedDict):
    result: Any
    error: Optional[str]


LOCAL_SERVER_PORT = 8766
LOCAL_SERVER_HOST = "127.0.0.1"
API_VERSION = 1

ALLOWED_ORIGINS = {SITE_URL_PROD, SITE_URL_DEV}


def _run_on_main_sync(fn: Any) -> Any:
    if not mw:
        raise RuntimeError("mw not available")
    future: concurrent.futures.Future[Any] = concurrent.futures.Future()

    def work() -> None:
        try:
            future.set_result(fn())
        except Exception as e:
            future.set_exception(e)

    mw.taskman.run_on_main(work)
    return future.result(timeout=30)


def _ok(result: Any) -> ApiResponse:
    return {"result": result, "error": None}


def _err(message: str) -> ApiResponse:
    return {"result": None, "error": message}


def _get_deck_id(params: Mapping[str, Any]) -> DeckId:
    raw = params.get("deckId")
    if raw is None:
        return GLOBAL_DECK_ID
    return cast(DeckId, int(raw))


class LocalServer:
    def __init__(self, processor: NoteProcessor) -> None:
        self._processor = processor
        self._thread: Optional[threading.Thread] = None
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._runner: Optional[web.AppRunner] = None
        self._actions: dict[str, Any] = {
            "ping": self._handle_ping,
            "getSmartFields": self._handle_get_smart_fields,
            "addSmartField": self._handle_add_smart_field,
            "updateSmartField": self._handle_update_smart_field,
            "removeSmartField": self._handle_remove_smart_field,
            "generateNote": self._handle_generate_note,
            "generateNotes": self._handle_generate_notes,
            "uiEditSmartField": self._handle_ui_edit_smart_field,
            "uiNewSmartField": self._handle_ui_new_smart_field,
        }

    def start(self) -> None:
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        if self._loop and self._runner:
            future = asyncio.run_coroutine_threadsafe(
                self._runner.cleanup(), self._loop
            )
            future.result(timeout=5)
        if self._loop:
            self._loop.call_soon_threadsafe(self._loop.stop)

    def _run(self) -> None:
        self._loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._loop)
        self._loop.run_until_complete(self._start_server())
        self._loop.run_forever()

    async def _start_server(self) -> None:
        app = web.Application()
        app.router.add_post("/", self._handle_request)
        app.router.add_post("/auth/callback", self._handle_auth_callback)
        app.router.add_options("/auth/callback", self._handle_auth_preflight)
        app.router.add_post("/subscription/refresh", self._handle_subscription_refresh)
        app.router.add_options("/subscription/refresh", self._handle_auth_preflight)
        app.router.add_post("/ping", self._handle_loopback_ping)
        app.router.add_options("/ping", self._handle_auth_preflight)
        self._runner = web.AppRunner(app)
        await self._runner.setup()
        try:
            site = web.TCPSite(self._runner, LOCAL_SERVER_HOST, LOCAL_SERVER_PORT)
            await site.start()
            logger.info(
                f"Local server started on http://{LOCAL_SERVER_HOST}:{LOCAL_SERVER_PORT}"
            )
        except OSError as e:
            # Port already in use (another Anki profile, or something squatting).
            # That user falls back to the auth code flow — acceptable edge case.
            logger.error(
                f"Local server failed to bind {LOCAL_SERVER_HOST}:{LOCAL_SERVER_PORT}: {e}"
            )

    def _cors_headers(self, origin: str) -> dict[str, str]:
        # Only called once origin is confirmed to be in ALLOWED_ORIGINS.
        return {
            "Access-Control-Allow-Origin": origin,
            "Access-Control-Allow-Methods": "POST, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type",
            "Access-Control-Allow-Private-Network": "true",
            "Access-Control-Max-Age": "600",
            "Vary": "Origin",
        }

    async def _handle_auth_preflight(self, request: web.Request) -> web.Response:
        origin = request.headers.get("Origin")
        if origin not in ALLOWED_ORIGINS:
            return web.Response(status=403)
        return web.Response(status=204, headers=self._cors_headers(origin))

    async def _handle_auth_callback(self, request: web.Request) -> web.Response:
        origin = request.headers.get("Origin")
        if origin not in ALLOWED_ORIGINS:
            logger.warning(f"Rejected /auth/callback from origin: {origin}")
            return web.json_response({"ok": False, "error": "forbidden"}, status=403)
        headers = self._cors_headers(origin)
        try:
            body = await request.json()
        except Exception:
            return web.json_response(
                {"ok": False, "error": "invalid_json"}, status=400, headers=headers
            )
        jwt = body.get("jwt")
        if not isinstance(jwt, str) or not jwt:
            return web.json_response(
                {"ok": False, "error": "missing_jwt"}, status=400, headers=headers
            )

        def write_token() -> None:
            config.auth_token = jwt
            if sentry:
                sentry.set_user()
            app_state.update_subscription_state()

        if mw:
            mw.taskman.run_on_main(write_token)
        return web.json_response({"ok": True}, headers=headers)

    async def _handle_subscription_refresh(self, request: web.Request) -> web.Response:
        origin = request.headers.get("Origin")
        if origin not in ALLOWED_ORIGINS:
            return web.json_response({"ok": False, "error": "forbidden"}, status=403)
        if mw:
            mw.taskman.run_on_main(app_state.update_subscription_state)
        return web.json_response({"ok": True}, headers=self._cors_headers(origin))

    async def _handle_loopback_ping(self, request: web.Request) -> web.Response:
        # Browser-reachable no-op. Site calls this first to surface the PNA
        # consent prompt explicitly, before posting the real JWT.
        origin = request.headers.get("Origin")
        if origin not in ALLOWED_ORIGINS:
            return web.json_response({"ok": False, "error": "forbidden"}, status=403)
        return web.json_response({"ok": True}, headers=self._cors_headers(origin))

    async def _handle_request(self, request: web.Request) -> web.Response:
        try:
            body = await request.json()
        except Exception:
            return web.json_response(_err("Invalid JSON"))

        action = body.get("action")
        version = body.get("version")
        params = body.get("params", {})

        if version != API_VERSION:
            return web.json_response(
                _err(f"Unsupported version: {version}, expected {API_VERSION}")
            )

        if action not in self._actions:
            return web.json_response(_err(f"Unknown action: {action}"))

        try:
            result = await self._actions[action](params)
            return web.json_response(result)
        except Exception as e:
            logger.error(
                f"Local server error handling {action}: "
                f"{''.join(traceback.format_exception(type(e), e, e.__traceback__))}"
            )
            return web.json_response(_err(str(e)))

    async def _handle_ping(self, params: dict[str, Any]) -> ApiResponse:
        return _ok("pong")

    async def _handle_get_smart_fields(
        self, params: GetSmartFieldsParams
    ) -> ApiResponse:
        note_type = params.get("noteType")
        if not note_type:
            return _err("noteType is required")

        deck_id = _get_deck_id(params)

        prompts = get_prompts_for_note(
            note_type, deck_id, fallback_to_global_deck=(deck_id == GLOBAL_DECK_ID)
        )
        if not prompts:
            return _ok({})

        result: dict[str, SmartFieldInfo] = {}
        for field, prompt in prompts.items():
            extras = get_extras(
                note_type=note_type,
                field=field,
                deck_id=deck_id,
            )
            result[field] = {"prompt": prompt, "extras": extras}

        return _ok(result)

    async def _handle_add_smart_field(self, params: SmartFieldParams) -> ApiResponse:
        note_type = params.get("noteType")
        field = params.get("field")
        prompt = params.get("prompt")
        field_type: SmartFieldType = params.get("type", "chat")

        if not note_type or not field or not prompt:
            return _err("noteType, field, and prompt are required")

        deck_id = _get_deck_id(params)

        existing = get_prompts_for_note(
            note_type, deck_id, fallback_to_global_deck=False
        )
        if existing and field in existing:
            return _err(
                f"Field '{field}' already exists for noteType '{note_type}' "
                f"and deckId {deck_id}"
            )

        return await self._save_smart_field(
            params, note_type, field, prompt, field_type, deck_id
        )

    async def _handle_update_smart_field(self, params: SmartFieldParams) -> ApiResponse:
        note_type = params.get("noteType")
        field = params.get("field")
        prompt = params.get("prompt")
        field_type: SmartFieldType = params.get("type", "chat")

        if not note_type or not field or not prompt:
            return _err("noteType, field, and prompt are required")

        deck_id = _get_deck_id(params)

        existing = get_prompts_for_note(
            note_type, deck_id, fallback_to_global_deck=False
        )
        if not existing or field not in existing:
            return _err(
                f"Field '{field}' does not exist for noteType '{note_type}' "
                f"and deckId {deck_id}"
            )

        return await self._save_smart_field(
            params, note_type, field, prompt, field_type, deck_id
        )

    async def _save_smart_field(
        self,
        params: SmartFieldParams,
        note_type: str,
        field: str,
        prompt: str,
        field_type: SmartFieldType,
        deck_id: DeckId,
    ) -> ApiResponse:
        is_automatic = params.get("automatic", True)
        use_custom_model = params.get("useCustomModel", False)

        chat_options: OverridableChatOptionsDict = {
            "chat_provider": params.get("chatOptions", {}).get("provider"),
            "chat_model": params.get("chatOptions", {}).get("model"),
            "chat_temperature": params.get("chatOptions", {}).get("temperature"),
            "chat_markdown_to_html": params.get("chatOptions", {}).get(
                "markdownToHtml"
            ),
            "chat_web_search": params.get("chatOptions", {}).get("webSearch"),
        }

        tts_options: OverrideableTTSOptionsDict = {
            "tts_provider": params.get("ttsOptions", {}).get("provider"),
            "tts_model": params.get("ttsOptions", {}).get("model"),
            "tts_voice": params.get("ttsOptions", {}).get("voice"),
            "tts_strip_html": params.get("ttsOptions", {}).get("stripHtml"),
        }

        image_options: OverridableImageOptionsDict = {
            "image_provider": params.get("imageOptions", {}).get("provider"),
            "image_model": params.get("imageOptions", {}).get("model"),
        }

        def do_save() -> None:
            new_map = add_or_update_prompts(
                prompts_map=config.prompts_map,
                note_type=note_type,
                deck_id=deck_id,
                field=field,
                prompt=prompt,
                is_automatic=is_automatic,
                is_custom_model=use_custom_model,
                type=field_type,
                tts_options=tts_options,
                chat_options=chat_options,
                image_options=image_options,
            )
            config.prompts_map = new_map

        _run_on_main_sync(do_save)
        return _ok(True)

    async def _handle_remove_smart_field(
        self, params: RemoveSmartFieldParams
    ) -> ApiResponse:
        note_type = params.get("noteType")
        field = params.get("field")

        if not note_type or not field:
            return _err("noteType and field are required")

        deck_id = _get_deck_id(params)

        def do_remove() -> None:
            new_map = remove_prompt(
                prompts_map=config.prompts_map,
                note_type=note_type,
                deck_id=deck_id,
                field=field,
            )
            config.prompts_map = new_map

        _run_on_main_sync(do_remove)
        return _ok(True)

    async def _handle_generate_note(self, params: GenerateNoteParams) -> ApiResponse:
        note_id_raw = params.get("noteId")
        if note_id_raw is None:
            return _err("noteId is required")

        if not mw or not mw.col:
            return _err("Anki collection not available")

        note_id = cast(NoteId, int(note_id_raw))
        note = mw.col.get_note(note_id)

        overwrite = params.get("overwrite", False)
        target_field = params.get("targetField")

        deck_id: Optional[DeckId] = None
        raw_deck = params.get("deckId")
        if raw_deck is not None:
            deck_id = cast(DeckId, int(raw_deck))
        else:
            cards = note.cards()
            if cards:
                deck_id = cards[0].did

        if deck_id is None:
            return _err("Could not determine deckId for note")

        fields_before = {f: note[f] for f in note.keys()}  # noqa: SIM118

        updated = await self._processor._process_note(  # type: ignore
            note,
            deck_id=deck_id,
            overwrite_fields=overwrite,
            target_field=target_field,
        )

        if updated:
            _run_on_main_sync(
                lambda: mw.col.update_note(note) if mw and mw.col else None
            )

        fields_after = {f: note[f] for f in note.keys()}  # noqa: SIM118
        changed_fields = {
            f: fields_after[f]
            for f in fields_after
            if fields_after[f] != fields_before.get(f)
        }

        result: GenerateNoteResult = {"updated": updated, "fields": changed_fields}
        return _ok(result)

    async def _handle_generate_notes(self, params: GenerateNotesParams) -> ApiResponse:
        note_ids_raw = params.get("noteIds")
        if not note_ids_raw:
            return _err("noteIds is required")

        if not mw or not mw.col:
            return _err("Anki collection not available")

        overwrite = params.get("overwrite", False)

        note_ids = [cast(NoteId, int(nid)) for nid in note_ids_raw]

        did_map: dict[NoteId, DeckId] = {}
        raw_deck = params.get("deckId")
        for nid in note_ids:
            if raw_deck is not None:
                did_map[nid] = cast(DeckId, int(raw_deck))
            else:
                note = mw.col.get_note(nid)
                cards = note.cards()
                if cards:
                    did_map[nid] = cards[0].did

        (
            updated_notes,
            failed_notes,
            skipped_notes,
        ) = await self._processor._process_notes_batch(  # type: ignore
            note_ids,
            overwrite_fields=overwrite,
            did_map=did_map,
        )

        if updated_notes:
            _run_on_main_sync(
                lambda: mw.col.update_notes(updated_notes) if mw and mw.col else None
            )

        result: GenerateNotesResult = {
            "updated": [n.id for n in updated_notes],
            "failed": [n.id for n in failed_notes],
            "skipped": [n.id for n in skipped_notes],
        }
        return _ok(result)

    async def _handle_ui_edit_smart_field(self, params: dict[str, Any]) -> ApiResponse:
        note_type = params.get("noteType")
        field = params.get("field")

        if not note_type or not field:
            return _err("noteType and field are required")

        deck_id = _get_deck_id(params)

        extras = get_extras(note_type=note_type, field=field, deck_id=deck_id)
        if not extras:
            return _err(f"No smart field '{field}' for noteType '{note_type}'")

        prompts = get_prompts_for_note(
            note_type=note_type,
            to_lower=True,
            deck_id=deck_id,
            fallback_to_global_deck=False,
        )

        all_fields = get_fields(note_type)
        if not prompts or field not in all_fields:
            return _err("Note type does not exist or field not in note type")

        field_type = extras["type"]

        def open_dialog() -> bool:
            def on_accept(new_map: Any) -> None:
                config.prompts_map = new_map

            dialog = PromptDialog(
                config.prompts_map,
                self._processor,
                on_accept,
                card_type=note_type,
                deck_id=deck_id,
                field=field,
                field_type=field_type,
                prompt=prompts[field.lower()],
            )
            return dialog.exec() == QDialog.DialogCode.Accepted

        accepted = _run_on_main_sync(open_dialog)
        return _ok(accepted)

    async def _handle_ui_new_smart_field(self, params: dict[str, Any]) -> ApiResponse:
        field_type: Optional[SmartFieldType] = params.get("fieldType")

        if not field_type or field_type not in ("chat", "tts", "image"):
            return _err("fieldType is required (chat, tts, or image)")

        deck_id = _get_deck_id(params)

        def open_dialog() -> bool:
            def on_accept(new_map: Any) -> None:
                config.prompts_map = new_map

            dialog = PromptDialog(
                config.prompts_map,
                self._processor,
                on_accept,
                field_type=field_type,
                deck_id=deck_id,
            )
            return dialog.exec() == QDialog.DialogCode.Accepted

        accepted = _run_on_main_sync(open_dialog)
        return _ok(accepted)
