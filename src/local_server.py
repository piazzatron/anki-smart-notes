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

# ruff: noqa: N815
#
# Request/response dataclasses mirror a camelCase JSON wire contract; dacite
# maps dict keys directly to dataclass field names, so the fields must match.

import asyncio
import concurrent.futures
import threading
import traceback
from collections.abc import Awaitable
from dataclasses import dataclass, field
from typing import Any, Callable, Optional, TypeVar, Union, cast

import dacite
from aiohttp import web
from anki.decks import DeckId
from anki.notes import NoteId
from aqt import mw
from aqt.qt import QDialog

from .app_state import app_state
from .config import config
from .constants import GLOBAL_DECK_ID, SITE_URL_DEV
from .logger import logger
from .models import (
    FieldExtras,
    OverridableChatOptionsDict,
    OverridableImageOptionsDict,
    OverrideableTTSOptionsDict,
    SmartFieldType,
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

# -- Public API --------------------------------------------------------------


class LocalServer:
    """Background aiohttp server that exposes the add-on to the signup web
    flow (CORS'd endpoints) and to local tooling (the `/` RPC dispatch)."""

    def __init__(self, processor: NoteProcessor) -> None:
        self._processor = processor
        self._thread: Optional[threading.Thread] = None
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._runner: Optional[web.AppRunner] = None

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
        self._loop.run_until_complete(self._serve())
        self._loop.run_forever()

    async def _serve(self) -> None:
        app = build_app(self._processor)
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


def build_app(processor: NoteProcessor) -> web.Application:
    """Construct the aiohttp Application. Exposed for tests."""
    app = web.Application(middlewares=[cors_middleware])
    _register_routes(app, processor)
    return app


# -- Constants ---------------------------------------------------------------


LOCAL_SERVER_PORT = 8766
LOCAL_SERVER_HOST = "127.0.0.1"
API_VERSION = 1

ALLOWED_ORIGINS: frozenset[str] = frozenset(
    {
        "https://smart-notes.xyz",
        "https://www.smart-notes.xyz",
        SITE_URL_DEV,
    }
)


# -- Request param types -----------------------------------------------------
#
# Parsed from request JSON bodies via `dacite.from_dict`. Missing required
# fields surface as ParamError("<field> is required"); wrong types surface
# via `dacite.WrongTypeError`.


@dataclass
class GetSmartFieldsParams:
    noteType: str
    deckId: Optional[int] = None


@dataclass
class ChatOptionsParams:
    provider: Optional[str] = None
    model: Optional[str] = None
    temperature: Optional[int] = None
    markdownToHtml: Optional[bool] = None
    webSearch: Optional[bool] = None


@dataclass
class TTSOptionsParams:
    provider: Optional[str] = None
    model: Optional[str] = None
    voice: Optional[str] = None
    stripHtml: Optional[bool] = None


@dataclass
class ImageOptionsParams:
    provider: Optional[str] = None
    model: Optional[str] = None


@dataclass
class SmartFieldParams:
    noteType: str
    field: str
    prompt: str
    type: SmartFieldType = "chat"
    deckId: Optional[int] = None
    automatic: bool = True
    useCustomModel: bool = False
    chatOptions: Optional[ChatOptionsParams] = None
    ttsOptions: Optional[TTSOptionsParams] = None
    imageOptions: Optional[ImageOptionsParams] = None


@dataclass
class RemoveSmartFieldParams:
    noteType: str
    field: str
    deckId: Optional[int] = None


@dataclass
class GenerateNoteParams:
    noteId: int
    deckId: Optional[int] = None
    overwrite: bool = False
    targetField: Optional[str] = None


@dataclass
class GenerateNotesParams:
    noteIds: list[int]
    deckId: Optional[int] = None
    overwrite: bool = False


@dataclass
class UiEditSmartFieldParams:
    noteType: str
    field: str
    deckId: Optional[int] = None


@dataclass
class UiNewSmartFieldParams:
    fieldType: SmartFieldType
    deckId: Optional[int] = None


@dataclass
class AuthCallbackBody:
    jwt: str


@dataclass
class RpcRequest:
    action: str
    version: int
    params: dict[str, Any] = field(default_factory=dict)


# -- Response envelope -------------------------------------------------------


@dataclass
class SmartFieldInfo:
    prompt: str
    extras: Optional[FieldExtras]


@dataclass
class GenerateNoteResult:
    updated: bool
    fields: dict[str, str]


@dataclass
class GenerateNotesResult:
    updated: list[int]
    failed: list[int]
    skipped: list[int]


def _envelope(result: Any = None, error: Optional[str] = None) -> web.Response:
    return web.json_response({"result": result, "error": error})


def _ok(result: Any = None) -> web.Response:
    return _envelope(result=result)


def _err(message: str) -> web.Response:
    return _envelope(error=message)


# -- CORS middleware ---------------------------------------------------------


@dataclass(frozen=True)
class CorsPolicy:
    """Declarative CORS config for a single path.

    `allowed_origins="*"` lets any origin through (used for the loopback ping
    that exists only to surface the PNA consent prompt — it has no side effects
    worth gating). A concrete set restricts to an allowlist and rejects
    everything else with a plain 403.
    """

    allowed_origins: Union[frozenset[str], str]
    allowed_methods: str

    def is_allowed(self, origin: Optional[str]) -> bool:
        if self.allowed_origins == "*":
            return True
        return origin is not None and origin in self.allowed_origins


_PNA_HEADER = "Access-Control-Allow-Private-Network"


def _cors_response_headers(policy: CorsPolicy, origin: Optional[str]) -> dict[str, str]:
    echoed = origin if policy.allowed_origins != "*" else (origin or "*")
    return {
        "Access-Control-Allow-Origin": echoed or "*",
        "Access-Control-Allow-Methods": f"{policy.allowed_methods}, OPTIONS",
        "Access-Control-Allow-Headers": "Content-Type",
        _PNA_HEADER: "true",
        "Access-Control-Max-Age": "600",
        "Vary": "Origin",
    }


@web.middleware
async def cors_middleware(
    request: web.Request,
    handler: Callable[[web.Request], Awaitable[web.StreamResponse]],
) -> web.StreamResponse:
    policy = CORS_POLICIES.get(request.path)

    # No CORS on this path — handle normally (e.g. the `/` RPC endpoint).
    if policy is None:
        return await handler(request)

    origin = request.headers.get("Origin")

    # Preflight: short-circuit without invoking the handler.
    if request.method == "OPTIONS":
        if not policy.is_allowed(origin):
            return web.Response(status=403)
        return web.Response(status=204, headers=_cors_response_headers(policy, origin))

    # Real request with a restricted origin: reject up front so the handler
    # never sees the caller. Matches the previous per-endpoint gating.
    if policy.allowed_origins != "*" and not policy.is_allowed(origin):
        logger.warning(f"Rejected {request.path} from origin: {origin}")
        return web.json_response({"ok": False, "error": "forbidden"}, status=403)

    response = await handler(request)
    response.headers.update(_cors_response_headers(policy, origin))
    return response


# Populated below once the policies' origin sets are known.
CORS_POLICIES: dict[str, CorsPolicy] = {
    "/auth/callback": CorsPolicy(ALLOWED_ORIGINS, "POST"),
    "/subscription/refresh": CorsPolicy(ALLOWED_ORIGINS, "POST"),
    "/ping": CorsPolicy("*", "GET"),
}


# -- Route registration ------------------------------------------------------


def _register_routes(app: web.Application, processor: NoteProcessor) -> None:
    # Browser-reachable endpoints. CORS middleware handles preflight; the
    # OPTIONS routes below exist so aiohttp matches them rather than 405ing
    # before middleware runs.
    app.router.add_post("/auth/callback", handle_auth_callback)
    app.router.add_options("/auth/callback", _options_stub)
    app.router.add_post("/subscription/refresh", handle_subscription_refresh)
    app.router.add_options("/subscription/refresh", _options_stub)
    app.router.add_get("/ping", handle_loopback_ping)
    app.router.add_options("/ping", _options_stub)

    # Action-dispatched RPC endpoint.
    app.router.add_post("/", make_rpc_handler(processor))


async def _options_stub(_: web.Request) -> web.Response:
    # Reached only if CORS middleware somehow misses — middleware always
    # intercepts OPTIONS for mapped paths.
    return web.Response(status=405)


# -- Browser-facing handlers -------------------------------------------------


async def handle_auth_callback(request: web.Request) -> web.Response:
    try:
        raw = await request.json()
    except Exception:
        return web.json_response({"ok": False, "error": "invalid_json"}, status=400)

    try:
        body = parse_params(AuthCallbackBody, raw)
    except ParamError:
        return web.json_response({"ok": False, "error": "missing_jwt"}, status=400)

    if not body.jwt:
        return web.json_response({"ok": False, "error": "missing_jwt"}, status=400)

    def write_token() -> None:
        config.auth_token = body.jwt
        if sentry:
            sentry.set_user()
        app_state.update_subscription_state()

    if mw:
        mw.taskman.run_on_main(write_token)
    return web.json_response({"ok": True})


async def handle_subscription_refresh(_: web.Request) -> web.Response:
    if mw:
        mw.taskman.run_on_main(app_state.update_subscription_state)
    return web.json_response({"ok": True})


async def handle_loopback_ping(_: web.Request) -> web.Response:
    # Browser-reachable no-op used to surface the PNA consent prompt on a
    # user gesture before the real JWT post. Intentionally unguarded —
    # no sensitive response, no side effect.
    return web.json_response({"ok": True})


# -- RPC dispatch ------------------------------------------------------------


def make_rpc_handler(
    processor: NoteProcessor,
) -> Callable[[web.Request], Awaitable[web.Response]]:
    """Build the `POST /` handler. Accepts `{action, version, params}` and
    dispatches to a registered action handler."""

    async def rpc_handler(request: web.Request) -> web.Response:
        try:
            raw = await request.json()
        except Exception:
            return _err("Invalid JSON")

        try:
            rpc = parse_params(RpcRequest, raw)
        except ParamError as e:
            return _err(str(e))

        if rpc.version != API_VERSION:
            return _err(f"Unsupported version: {rpc.version}, expected {API_VERSION}")

        handler = ACTIONS.get(rpc.action)
        if handler is None:
            return _err(f"Unknown action: {rpc.action}")

        try:
            return await handler(processor, rpc.params)
        except ParamError as e:
            return _err(str(e))
        except Exception as e:
            logger.error(
                f"Local server error handling {rpc.action}: "
                f"{''.join(traceback.format_exception(type(e), e, e.__traceback__))}"
            )
            return _err(str(e))

    return rpc_handler


# -- Action handlers ---------------------------------------------------------


async def action_ping(_: NoteProcessor, __: dict[str, Any]) -> web.Response:
    return _ok("pong")


async def action_get_smart_fields(
    _: NoteProcessor, raw: dict[str, Any]
) -> web.Response:
    params = parse_params(GetSmartFieldsParams, raw)
    deck_id = _resolve_deck_id(params.deckId)

    prompts = get_prompts_for_note(
        params.noteType,
        deck_id,
        fallback_to_global_deck=(deck_id == GLOBAL_DECK_ID),
    )
    if not prompts:
        return _ok({})

    result: dict[str, dict[str, Any]] = {}
    for field_name, prompt in prompts.items():
        extras = get_extras(
            note_type=params.noteType, field=field_name, deck_id=deck_id
        )
        result[field_name] = {"prompt": prompt, "extras": extras}

    return _ok(result)


async def action_add_smart_field(_: NoteProcessor, raw: dict[str, Any]) -> web.Response:
    params = parse_params(SmartFieldParams, raw)
    deck_id = _resolve_deck_id(params.deckId)

    existing = get_prompts_for_note(
        params.noteType, deck_id, fallback_to_global_deck=False
    )
    if existing and params.field in existing:
        return _err(
            f"Field '{params.field}' already exists for noteType "
            f"'{params.noteType}' and deckId {deck_id}"
        )

    return _save_smart_field(params, deck_id)


async def action_update_smart_field(
    _: NoteProcessor, raw: dict[str, Any]
) -> web.Response:
    params = parse_params(SmartFieldParams, raw)
    deck_id = _resolve_deck_id(params.deckId)

    existing = get_prompts_for_note(
        params.noteType, deck_id, fallback_to_global_deck=False
    )
    if not existing or params.field not in existing:
        return _err(
            f"Field '{params.field}' does not exist for noteType "
            f"'{params.noteType}' and deckId {deck_id}"
        )

    return _save_smart_field(params, deck_id)


async def action_remove_smart_field(
    _: NoteProcessor, raw: dict[str, Any]
) -> web.Response:
    params = parse_params(RemoveSmartFieldParams, raw)
    deck_id = _resolve_deck_id(params.deckId)

    def do_remove() -> None:
        config.prompts_map = remove_prompt(
            prompts_map=config.prompts_map,
            note_type=params.noteType,
            deck_id=deck_id,
            field=params.field,
        )

    _run_on_main_sync(do_remove)
    return _ok(True)


async def action_generate_note(
    processor: NoteProcessor, raw: dict[str, Any]
) -> web.Response:
    params = parse_params(GenerateNoteParams, raw)

    if not mw or not mw.col:
        return _err("Anki collection not available")

    note_id = cast(NoteId, params.noteId)
    note = mw.col.get_note(note_id)

    deck_id: Optional[DeckId] = None
    if params.deckId is not None:
        deck_id = cast(DeckId, params.deckId)
    else:
        cards = note.cards()
        if cards:
            deck_id = cards[0].did

    if deck_id is None:
        return _err("Could not determine deckId for note")

    fields_before = {f: note[f] for f in note.keys()}  # noqa: SIM118

    updated = await processor._process_note(  # type: ignore[attr-defined]
        note,
        deck_id=deck_id,
        overwrite_fields=params.overwrite,
        target_field=params.targetField,
    )

    if updated:
        _run_on_main_sync(lambda: mw.col.update_note(note) if mw and mw.col else None)

    fields_after = {f: note[f] for f in note.keys()}  # noqa: SIM118
    changed_fields = {
        f: fields_after[f]
        for f in fields_after
        if fields_after[f] != fields_before.get(f)
    }

    return _ok({"updated": updated, "fields": changed_fields})


async def action_generate_notes(
    processor: NoteProcessor, raw: dict[str, Any]
) -> web.Response:
    params = parse_params(GenerateNotesParams, raw)

    if not params.noteIds:
        return _err("noteIds is required")

    if not mw or not mw.col:
        return _err("Anki collection not available")

    note_ids = [cast(NoteId, nid) for nid in params.noteIds]

    did_map: dict[NoteId, DeckId] = {}
    for nid in note_ids:
        if params.deckId is not None:
            did_map[nid] = cast(DeckId, params.deckId)
        else:
            cards = mw.col.get_note(nid).cards()
            if cards:
                did_map[nid] = cards[0].did

    (
        updated_notes,
        failed_notes,
        skipped_notes,
    ) = await processor._process_notes_batch(  # type: ignore[attr-defined]
        note_ids,
        overwrite_fields=params.overwrite,
        did_map=did_map,
    )

    if updated_notes:
        _run_on_main_sync(
            lambda: mw.col.update_notes(updated_notes) if mw and mw.col else None
        )

    return _ok(
        {
            "updated": [n.id for n in updated_notes],
            "failed": [n.id for n in failed_notes],
            "skipped": [n.id for n in skipped_notes],
        }
    )


async def action_ui_edit_smart_field(
    processor: NoteProcessor, raw: dict[str, Any]
) -> web.Response:
    params = parse_params(UiEditSmartFieldParams, raw)
    deck_id = _resolve_deck_id(params.deckId)

    extras = get_extras(note_type=params.noteType, field=params.field, deck_id=deck_id)
    if not extras:
        return _err(f"No smart field '{params.field}' for noteType '{params.noteType}'")

    prompts = get_prompts_for_note(
        note_type=params.noteType,
        to_lower=True,
        deck_id=deck_id,
        fallback_to_global_deck=False,
    )
    all_fields = get_fields(params.noteType)
    if not prompts or params.field not in all_fields:
        return _err("Note type does not exist or field not in note type")

    field_type = extras["type"]

    def open_dialog() -> bool:
        def on_accept(new_map: Any) -> None:
            config.prompts_map = new_map

        dialog = PromptDialog(
            config.prompts_map,
            processor,
            on_accept,
            card_type=params.noteType,
            deck_id=deck_id,
            field=params.field,
            field_type=field_type,
            prompt=prompts[params.field.lower()],
        )
        return dialog.exec() == QDialog.DialogCode.Accepted

    return _ok(_run_on_main_sync(open_dialog))


async def action_ui_new_smart_field(
    processor: NoteProcessor, raw: dict[str, Any]
) -> web.Response:
    params = parse_params(UiNewSmartFieldParams, raw)
    deck_id = _resolve_deck_id(params.deckId)

    def open_dialog() -> bool:
        def on_accept(new_map: Any) -> None:
            config.prompts_map = new_map

        dialog = PromptDialog(
            config.prompts_map,
            processor,
            on_accept,
            field_type=params.fieldType,
            deck_id=deck_id,
        )
        return dialog.exec() == QDialog.DialogCode.Accepted

    return _ok(_run_on_main_sync(open_dialog))


# -- Action registry ---------------------------------------------------------


ActionHandler = Callable[[NoteProcessor, dict[str, Any]], Awaitable[web.Response]]

ACTIONS: dict[str, ActionHandler] = {
    "ping": action_ping,
    "getSmartFields": action_get_smart_fields,
    "addSmartField": action_add_smart_field,
    "updateSmartField": action_update_smart_field,
    "removeSmartField": action_remove_smart_field,
    "generateNote": action_generate_note,
    "generateNotes": action_generate_notes,
    "uiEditSmartField": action_ui_edit_smart_field,
    "uiNewSmartField": action_ui_new_smart_field,
}


# -- Helpers -----------------------------------------------------------------


T = TypeVar("T")


class ParamError(Exception):
    """Raised when request params fail dacite validation. The message is
    safe to surface to callers — it only names the offending field."""


def parse_params(cls: type[T], raw: Any) -> T:
    if not isinstance(raw, dict):
        raise ParamError("Request body must be a JSON object")
    try:
        return dacite.from_dict(data_class=cls, data=raw)
    except dacite.MissingValueError as e:
        raise ParamError(f"{e.field_path} is required") from e
    except dacite.WrongTypeError as e:
        raise ParamError(f"Invalid type for field '{e.field_path}'") from e
    except dacite.DaciteError as e:
        raise ParamError(str(e)) from e


def _resolve_deck_id(raw: Optional[int]) -> DeckId:
    if raw is None:
        return GLOBAL_DECK_ID
    return cast(DeckId, int(raw))


def _run_on_main_sync(fn: Callable[[], Any]) -> Any:
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


def _save_smart_field(params: SmartFieldParams, deck_id: DeckId) -> web.Response:
    # Cast incoming strings to the strongly-typed Literal unions the config
    # layer expects. We intentionally accept any string at the boundary — see
    # the note above the dataclasses for why.
    chat = params.chatOptions
    tts = params.ttsOptions
    image = params.imageOptions

    chat_options: OverridableChatOptionsDict = {
        "chat_provider": cast(Any, chat.provider) if chat else None,
        "chat_model": cast(Any, chat.model) if chat else None,
        "chat_temperature": chat.temperature if chat else None,
        "chat_markdown_to_html": chat.markdownToHtml if chat else None,
        "chat_web_search": chat.webSearch if chat else None,
    }

    tts_options: OverrideableTTSOptionsDict = {
        "tts_provider": cast(Any, tts.provider) if tts else None,
        "tts_model": cast(Any, tts.model) if tts else None,
        "tts_voice": tts.voice if tts else None,
        "tts_strip_html": tts.stripHtml if tts else None,
    }

    image_options: OverridableImageOptionsDict = {
        "image_provider": cast(Any, image.provider) if image else None,
        "image_model": cast(Any, image.model) if image else None,
    }

    def do_save() -> None:
        config.prompts_map = add_or_update_prompts(
            prompts_map=config.prompts_map,
            note_type=params.noteType,
            deck_id=deck_id,
            field=params.field,
            prompt=params.prompt,
            is_automatic=params.automatic,
            is_custom_model=params.useCustomModel,
            type=params.type,
            tts_options=tts_options,
            chat_options=chat_options,
            image_options=image_options,
        )

    _run_on_main_sync(do_save)
    return _ok(True)
