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
import inspect
import json
import secrets
import sys
import threading
from collections.abc import Callable
from pathlib import Path
from typing import Any, Optional

from aiohttp import web
from aqt import mw

from . import env
from .api_client import api
from .app_state import app_state
from .config import config
from .constants import SITE_URL_DEV
from .decks import deck_id_to_name_map
from .event_bus import (
    BrowserSelectionChanged,
    StateInvalidated,
    WebEvent,
    event_bus,
)
from .feature_flags import flags
from .logger import logger
from .sentry import sentry
from .services import auth_service, settings_service
from .services.prompt_test_service import (
    prepare_image_prompt_test,
    prepare_text_prompt_test,
    prepare_tts_prompt_test,
    run_image_prompt_test,
    run_text_prompt_test,
    run_tts_prompt_test,
    save_test_result,
)
from .services.smart_field_service import smart_field_service
from .telemetry import track_event
from .ui.ui_utils import open_anki_browser
from .utils import get_version
from .utils.notes_utils import get_note_types_with_fields
from .web import dto

LOCAL_SERVER_PORT = 8766
LOCAL_SERVER_HOST = "127.0.0.1"

WEB_APP_STATIC_DIR = Path(__file__).parent / "web" / "static"

ALLOWED_ORIGINS = {
    "https://smart-notes.xyz",
    "https://www.smart-notes.xyz",
    SITE_URL_DEV,
}


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


class LocalServer:
    def __init__(self) -> None:
        # Production webviews use a per-profile capability token. Dev builds
        # deliberately allow browser-driven testing through the fixed port.
        self.session_token = secrets.token_urlsafe(32)
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
        self._loop.run_until_complete(self._start_server())
        self._loop.run_forever()

    async def _start_server(self) -> None:
        app = web.Application()
        app.router.add_post("/auth/callback", self._handle_auth_callback)
        app.router.add_options("/auth/callback", self._handle_auth_preflight)
        app.router.add_post("/subscription/refresh", self._handle_subscription_refresh)
        app.router.add_options("/subscription/refresh", self._handle_auth_preflight)
        app.router.add_get("/ping", self._handle_loopback_ping)
        app.router.add_options("/ping", self._handle_ping_preflight)
        app.router.add_get("/api/events", self._handle_events)
        app.router.add_post("/api/command", self._handle_command)
        app.router.add_get("/app/voice-catalog.json", self._handle_voice_catalog)
        app.router.add_get("/app", self._handle_app_index)
        app.router.add_get("/app/", self._handle_app_index)
        if WEB_APP_STATIC_DIR.exists():
            app.router.add_static("/app", WEB_APP_STATIC_DIR)
        self._runner = web.AppRunner(app)
        await self._runner.setup()
        try:
            # Short shutdown timeout: open SSE streams never finish on their
            # own and would otherwise hold graceful shutdown for 60s while
            # stop() only waits 5.
            site = web.TCPSite(
                self._runner,
                LOCAL_SERVER_HOST,
                LOCAL_SERVER_PORT,
                shutdown_timeout=0.5,
            )
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
            app_state.update_account_state()

        if mw:
            mw.taskman.run_on_main(write_token)
        return web.json_response({"ok": True}, headers=headers)

    async def _handle_subscription_refresh(self, request: web.Request) -> web.Response:
        origin = request.headers.get("Origin")
        if origin not in ALLOWED_ORIGINS:
            return web.json_response({"ok": False, "error": "forbidden"}, status=403)
        if mw:
            mw.taskman.run_on_main(app_state.update_account_state)
        return web.json_response({"ok": True}, headers=self._cors_headers(origin))

    async def _handle_loopback_ping(self, request: web.Request) -> web.Response:
        # Browser-reachable no-op used to surface the PNA consent prompt on a
        # user gesture before the real JWT post. No origin allowlist — the
        # response carries no sensitive info and no side effect.
        origin = request.headers.get("Origin", "*")
        return web.json_response({"ok": True}, headers=self._cors_headers(origin))

    async def _handle_ping_preflight(self, request: web.Request) -> web.Response:
        origin = request.headers.get("Origin", "*")
        return web.Response(status=204, headers=self._cors_headers(origin))

    def _check_api_auth(self, request: web.Request) -> Optional[web.Response]:
        # Hostname check defeats DNS rebinding: a malicious page can point its
        # own hostname at 127.0.0.1, but the browser still sends that hostname
        # in the Host header.
        hostname = request.host.rsplit(":", 1)[0]
        if hostname not in ("127.0.0.1", "localhost"):
            return web.Response(status=403)

        # Dev builds are driven directly from Vite in a browser. The fixed
        # loopback port identifies the real plugin server while test servers
        # and production builds continue through session authentication.
        if env.environment == "DEV" and request.host in {
            f"127.0.0.1:{LOCAL_SERVER_PORT}",
            f"localhost:{LOCAL_SERVER_PORT}",
        }:
            return None

        # Query param because EventSource can't set headers; header for the
        # rest of /api/*.
        token = request.query.get("token") or request.headers.get("X-Session-Token")
        if not token or not secrets.compare_digest(token, self.session_token):
            return web.Response(status=401)
        return None

    async def _handle_events(self, request: web.Request) -> web.StreamResponse:
        # web.Response is a MutableMapping, and an empty one is falsy — the
        # None check is load-bearing.
        denied = self._check_api_auth(request)
        if denied is not None:
            return denied

        response = web.StreamResponse(
            headers={
                "Content-Type": "text/event-stream",
                "Cache-Control": "no-cache",
            }
        )
        await response.prepare(request)

        queue: asyncio.Queue[WebEvent] = asyncio.Queue()
        event_bus.subscribe(asyncio.get_running_loop(), queue)
        try:
            # The snapshot is the head of the stream: clients build their
            # entire model from this connection, so no read endpoints exist.
            await self._send_state(response)
            await self._send_catalog(response)

            while True:
                # Drain the queue as a batch and coalesce: only the newest
                # selection matters, and any number of invalidations becomes
                # a single state push.
                events = [await queue.get()]
                while not queue.empty():
                    events.append(queue.get_nowait())

                selections = [
                    e for e in events if isinstance(e, BrowserSelectionChanged)
                ]
                if selections:
                    payload = json.dumps(selections[-1].payload)
                    await response.write(
                        f"event: anki.browserSelectionChanged\ndata: {payload}\n\n".encode()
                    )
                if any(isinstance(e, StateInvalidated) for e in events):
                    await self._send_state(response)
        except (ConnectionResetError, ConnectionError):
            pass  # Client disconnected
        finally:
            event_bus.unsubscribe(queue)
        return response

    async def _send_state(self, response: web.StreamResponse) -> None:
        # Gather one coherent domain snapshot on Anki's main thread; the
        # executor hop keeps the wait from blocking this event loop.
        state = await asyncio.get_running_loop().run_in_executor(
            None,
            lambda: _run_on_main_sync(
                lambda: dto.build_state(
                    defaults=smart_field_service.get_generation_defaults(),
                    note_types=get_note_types_with_fields(),
                    decks=deck_id_to_name_map(),
                    smart_fields=smart_field_service.get_all_smart_fields(),
                    account=app_state.state,
                    feature_flags=flags,
                    settings=dto.build_settings(),
                    app_version=get_version(),
                )
            ),
        )
        await response.write(f"event: state\ndata: {json.dumps(state)}\n\n".encode())

    async def _send_catalog(self, response: web.StreamResponse) -> None:
        await response.write(
            f"event: catalog\ndata: {json.dumps(dto.build_catalog())}\n\n".encode()
        )

    async def _handle_command(self, request: web.Request) -> web.Response:
        # Commands return only ack/validation errors: clients learn the new
        # state from the event stream, never from command responses.
        denied = self._check_api_auth(request)
        if denied is not None:
            return denied

        try:
            body = await request.json()
        except Exception:
            return web.json_response({"ok": False, "error": "invalid_json"}, status=400)

        command = body.get("command")
        handler = COMMAND_HANDLERS.get(command)
        if handler is None:
            # List valid commands so agents/tooling self-correct in one trip.
            return web.json_response(
                {
                    "ok": False,
                    "error": f"Unknown command: {command}. "
                    f"Valid commands: {', '.join(sorted(COMMAND_HANDLERS))}",
                },
                status=400,
            )

        logger.debug(f"Web command: {command}")
        payload = body.get("payload", {})
        try:
            # Synchronous handlers run as one main-thread unit. Async handlers
            # own their narrower main-thread hops around Anki state access.
            if inspect.iscoroutinefunction(handler):
                result = await handler(payload)
            else:
                result = await asyncio.get_running_loop().run_in_executor(
                    None, lambda: _run_on_main_sync(lambda: handler(payload))
                )
        except (ValueError, KeyError) as e:
            # KeyError: a trusted-client payload missing an expected wire key.
            return web.json_response({"ok": False, "error": str(e)}, status=400)
        except Exception as e:
            logger.exception(f"Web command failed: {command}")
            return web.json_response({"ok": False, "error": str(e)}, status=500)

        response: dict[str, Any] = {"ok": True}
        if result is not None:
            response["result"] = result
        return web.json_response(response)

    async def _handle_app_index(self, request: web.Request) -> web.StreamResponse:
        index = WEB_APP_STATIC_DIR / "index.html"
        if not index.exists():
            return web.Response(
                status=404,
                text="Smart Notes web app is not built. Run `bun run build` in web/.",
            )
        return web.FileResponse(index)

    async def _handle_voice_catalog(self, request: web.Request) -> web.Response:
        return web.json_response(dto.build_voice_catalog())


# -- Command dispatch: wire payload → dto parse → service call. Each runner
# must be called on the main thread; ValueError surfaces as a 400. The
# service's @republish_state decorator pushes fresh state to clients. --


def _run_create_smart_field(payload: dict[str, Any]) -> None:
    smart_field_service.create_smart_field(dto.parse_smart_field_create(payload))


def _run_update_smart_field(payload: dict[str, Any]) -> None:
    smart_field_service.update_smart_field(dto.parse_smart_field_update(payload))


def _run_delete_smart_field(payload: dict[str, Any]) -> None:
    smart_field_service.delete_smart_field(dto.parse_smart_field_id(payload))


def _run_save_defaults(payload: dict[str, Any]) -> None:
    defaults = dto.parse_generation_defaults(payload)
    smart_field_service.save_chat_defaults(defaults.chat)
    smart_field_service.save_tts_defaults(defaults.tts)
    smart_field_service.save_image_defaults(defaults.image)


def _run_save_chat_defaults(payload: dict[str, Any]) -> None:
    smart_field_service.save_chat_defaults(dto.parse_chat_generation_settings(payload))


def _run_save_image_defaults(payload: dict[str, Any]) -> None:
    smart_field_service.save_image_defaults(
        dto.parse_image_generation_settings(payload)
    )


def _run_save_tts_defaults(payload: dict[str, Any]) -> None:
    smart_field_service.save_tts_defaults(dto.parse_tts_generation_settings(payload))


def _run_save_settings(payload: dict[str, Any]) -> None:
    settings_service.save_settings(dto.parse_settings(payload))


async def _run_test_prompt(payload: dict[str, Any]) -> dict[str, str]:
    request = dto.parse_text_prompt_test(payload)
    context = await asyncio.get_running_loop().run_in_executor(
        None,
        lambda: _run_on_main_sync(lambda: prepare_text_prompt_test(request)),
    )
    return await run_text_prompt_test(context)


async def _run_test_image(payload: dict[str, Any]) -> dict[str, str]:
    request = dto.parse_image_prompt_test(payload)
    context = await asyncio.get_running_loop().run_in_executor(
        None,
        lambda: _run_on_main_sync(lambda: prepare_image_prompt_test(request)),
    )
    return await run_image_prompt_test(context)


async def _run_test_tts(payload: dict[str, Any]) -> dict[str, str]:
    request = dto.parse_tts_prompt_test(payload)
    context = await asyncio.get_running_loop().run_in_executor(
        None,
        lambda: _run_on_main_sync(lambda: prepare_tts_prompt_test(request)),
    )
    return await run_tts_prompt_test(context)


def _run_save_test_result(payload: dict[str, Any]) -> None:
    save_test_result(dto.parse_save_test_result(payload))


async def _run_generate_prompt(payload: dict[str, Any]) -> dict[str, str]:
    request = dto.parse_prompt_generate(payload)
    args = await asyncio.get_running_loop().run_in_executor(
        None,
        lambda: _run_on_main_sync(lambda: _prepare_prompt_generate_args(request)),
    )
    response = await api.get_api_response(
        path="prompt/generate",
        args=args,
        timeout_sec=30,
    )
    body = await response.json()
    if not isinstance(body, dict) or not isinstance(body.get("prompt"), str):
        raise RuntimeError("Prompt generation returned an invalid response")
    return {"prompt": body["prompt"]}


async def _run_send_feedback(payload: dict[str, Any]) -> None:
    message = dto.parse_feedback_message(payload)
    args = await asyncio.get_running_loop().run_in_executor(
        None,
        lambda: _run_on_main_sync(lambda: _prepare_feedback_args(message)),
    )
    await api.get_api_response(path="feedback", args=args)


def _run_logout(payload: dict[str, Any]) -> None:
    dto.parse_auth_logout(payload)
    auth_service.logout()


async def _run_exchange_auth_code(payload: dict[str, Any]) -> None:
    jwt = await auth_service.exchange_auth_code(dto.parse_auth_exchange_code(payload))

    # Authentication state belongs to Anki's main thread even though the code
    # exchange itself is an ordinary async network request.
    def store_token() -> None:
        config.auth_token = jwt
        if sentry:
            sentry.set_user()
        app_state.update_account_state()

    await asyncio.get_running_loop().run_in_executor(
        None, lambda: _run_on_main_sync(store_token)
    )


def _run_refresh_account(payload: dict[str, Any]) -> None:
    dto.parse_account_refresh(payload)
    auth_service.refresh_account()


def _run_open_browser(payload: dict[str, Any]) -> None:
    dto.parse_ui_open_browser(payload)
    open_anki_browser()


def _run_track_analytics_event(payload: dict[str, Any]) -> None:
    event, properties = dto.parse_analytics_event(payload)
    track_event(event, properties)


# Command names are namespaced like event names (state, anki.*): the protocol
# is typed messages in both directions over one channel each way.
COMMAND_HANDLERS: dict[str, Callable[[dict[str, Any]], Any]] = {
    "smartFields.create": _run_create_smart_field,
    "smartFields.update": _run_update_smart_field,
    "smartFields.delete": _run_delete_smart_field,
    "defaults.save": _run_save_defaults,
    "defaults.chat.save": _run_save_chat_defaults,
    "defaults.image.save": _run_save_image_defaults,
    "defaults.tts.save": _run_save_tts_defaults,
    "settings.save": _run_save_settings,
    "prompts.generate": _run_generate_prompt,
    "prompts.test": _run_test_prompt,
    "images.test": _run_test_image,
    "tts.test": _run_test_tts,
    "notes.saveTestResult": _run_save_test_result,
    "support.sendFeedback": _run_send_feedback,
    "account.refresh": _run_refresh_account,
    "auth.exchangeCode": _run_exchange_auth_code,
    "auth.logout": _run_logout,
    "ui.openBrowser": _run_open_browser,
    "analytics.track": _run_track_analytics_event,
}


def _prepare_prompt_generate_args(
    request: dto.PromptGenerateRequest,
) -> dict[str, Any]:
    note_type = next(
        (
            (name, fields)
            for note_type_id, name, fields in get_note_types_with_fields()
            if note_type_id == request.note_type_id
        ),
        None,
    )
    if note_type is None:
        raise ValueError(f"Unknown noteTypeId: {request.note_type_id}")

    deck_name = deck_id_to_name_map().get(request.deck_id)
    if deck_name is None:
        raise ValueError(f"Unknown deckId: {request.deck_id}")

    note_type_name, fields = note_type
    return {
        "note_type": note_type_name,
        "deck_name": deck_name,
        "target_field": request.target_field_name,
        "field_type": request.field_type,
        "fields": fields,
        "generation_prompt": request.generation_prompt,
    }


def _prepare_feedback_args(message: str) -> dict[str, str]:
    if not config.auth_token:
        raise ValueError("You must be signed in to send feedback")
    return {
        "message": message,
        "version": get_version(),
        "platform": sys.platform,
    }
