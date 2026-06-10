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
import json
import secrets
import threading
from pathlib import Path
from typing import Any, Optional

from aiohttp import web
from aqt import mw

from .app_state import app_state
from .config import config
from .constants import SITE_URL_DEV
from .logger import logger
from .sentry import sentry
from .web import commands, dto
from .web.event_bus import (
    BrowserSelectionChanged,
    StateInvalidated,
    WebEvent,
    event_bus,
)

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
        # Per-profile-load secret gating /api/*. Any local process or webpage
        # can reach this port; only the webview we open knows the token.
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
        app.router.add_post(
            "/api/commands/smart-fields/save", self._handle_save_smart_field
        )
        app.router.add_post(
            "/api/commands/smart-fields/delete", self._handle_delete_smart_field
        )
        app.router.add_post("/api/commands/defaults/save", self._handle_save_defaults)
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

            while True:
                # Drain the queue as a batch so rapid invalidations coalesce
                # into a single state push.
                events = [await queue.get()]
                while not queue.empty():
                    events.append(queue.get_nowait())

                for event in events:
                    if isinstance(event, BrowserSelectionChanged):
                        await self._send_sse(
                            response, "anki.browserSelectionChanged", event.payload
                        )
                if any(isinstance(e, StateInvalidated) for e in events):
                    await self._send_state(response)
        except (ConnectionResetError, ConnectionError):
            pass  # Client disconnected
        finally:
            event_bus.unsubscribe(queue)
        return response

    async def _send_state(self, response: web.StreamResponse) -> None:
        # build_state reads Anki/domain state, so it runs on the main thread;
        # the executor hop keeps the wait from blocking this event loop.
        state = await asyncio.get_running_loop().run_in_executor(
            None, lambda: _run_on_main_sync(dto.build_state)
        )
        await self._send_sse(response, "state", state)

    async def _send_sse(
        self, response: web.StreamResponse, event: str, data: Any
    ) -> None:
        await response.write(f"event: {event}\ndata: {json.dumps(data)}\n\n".encode())

    async def _handle_save_smart_field(self, request: web.Request) -> web.Response:
        return await self._run_command(
            request,
            lambda payload: commands.save_smart_field(
                dto.parse_smart_field_create(payload)
            ),
        )

    async def _handle_delete_smart_field(self, request: web.Request) -> web.Response:
        def run(payload: dict[str, Any]) -> None:
            ref = dto.parse_smart_field_ref(payload)
            commands.delete_smart_field(
                ref.note_type_id, ref.deck_id, ref.target_field_name
            )

        return await self._run_command(request, run)

    async def _handle_save_defaults(self, request: web.Request) -> web.Response:
        return await self._run_command(
            request,
            lambda payload: commands.save_generation_defaults(
                dto.parse_generation_defaults(payload)
            ),
        )

    async def _run_command(self, request: web.Request, run: Any) -> web.Response:
        # Commands return only ack/validation errors: clients learn the new
        # state from the event stream, never from command responses.
        denied = self._check_api_auth(request)
        if denied is not None:
            return denied

        try:
            payload = await request.json()
        except Exception:
            return web.json_response({"ok": False, "error": "invalid_json"}, status=400)

        try:
            # Parsing and the command both read/write domain state, so the
            # whole unit runs on the main thread; the executor hop keeps the
            # wait from blocking this event loop.
            await asyncio.get_running_loop().run_in_executor(
                None, lambda: _run_on_main_sync(lambda: run(payload))
            )
        except ValueError as e:
            return web.json_response({"ok": False, "error": str(e)}, status=400)
        return web.json_response({"ok": True})

    async def _handle_app_index(self, request: web.Request) -> web.StreamResponse:
        index = WEB_APP_STATIC_DIR / "index.html"
        if not index.exists():
            return web.Response(
                status=404,
                text="Smart Notes web app is not built. Run `bun run build` in web/.",
            )
        return web.FileResponse(index)
