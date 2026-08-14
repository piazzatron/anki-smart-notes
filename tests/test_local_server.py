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

import json
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer


def _make_server():
    from src.local_server import LocalServer

    return LocalServer()


def _make_app(server=None):
    server = server or _make_server()
    app = web.Application()
    app.router.add_post("/auth/callback", server._handle_auth_callback)
    app.router.add_options("/auth/callback", server._handle_auth_preflight)
    app.router.add_get("/ping", server._handle_loopback_ping)
    app.router.add_options("/ping", server._handle_ping_preflight)
    app.router.add_get("/api/events", server._handle_events)
    app.router.add_post("/api/command", server._handle_command)
    app.router.add_get("/app/voice-catalog.json", server._handle_voice_catalog)
    return app


ALLOWED_ORIGIN = "https://smart-notes.xyz"


# -- /auth/callback --


def _patch_auth_callback_deps(monkeypatch):
    """Replace config/sentry/app_state so _handle_auth_callback is pure."""
    import src.local_server

    written: dict[str, Any] = {"jwt": None, "did_refresh": False}

    class FakeConfig:
        auth_token = None

    fake_config = FakeConfig()
    fake_app_state = MagicMock()

    def fake_run_on_main(fn):
        fn()
        written["jwt"] = fake_config.auth_token
        written["did_refresh"] = fake_app_state.update_account_state.call_count == 1

    fake_mw = MagicMock()
    fake_mw.taskman.run_on_main = fake_run_on_main
    monkeypatch.setattr(src.local_server, "config", fake_config)
    monkeypatch.setattr(src.local_server, "mw", fake_mw)
    monkeypatch.setattr(src.local_server, "sentry", None)
    monkeypatch.setattr(src.local_server, "app_state", fake_app_state)
    return written


@pytest.mark.asyncio
async def test_auth_callback_happy_path(monkeypatch):
    written = _patch_auth_callback_deps(monkeypatch)

    async with TestClient(TestServer(_make_app())) as client:
        resp = await client.post(
            "/auth/callback",
            json={"jwt": "abc.def.ghi"},
            headers={"Origin": ALLOWED_ORIGIN},
        )
        assert resp.status == 200
        assert (await resp.json()) == {"ok": True}
        assert resp.headers["Access-Control-Allow-Origin"] == ALLOWED_ORIGIN
        assert written["jwt"] == "abc.def.ghi"
        assert written["did_refresh"] is True


@pytest.mark.asyncio
async def test_auth_callback_rejects_bad_origin(monkeypatch):
    _patch_auth_callback_deps(monkeypatch)

    async with TestClient(TestServer(_make_app())) as client:
        resp = await client.post(
            "/auth/callback",
            json={"jwt": "abc.def.ghi"},
            headers={"Origin": "https://evil.com"},
        )
        assert resp.status == 403
        assert "Access-Control-Allow-Origin" not in resp.headers


@pytest.mark.asyncio
async def test_auth_callback_rejects_missing_origin(monkeypatch):
    _patch_auth_callback_deps(monkeypatch)

    async with TestClient(TestServer(_make_app())) as client:
        resp = await client.post("/auth/callback", json={"jwt": "abc.def.ghi"})
        assert resp.status == 403


@pytest.mark.asyncio
async def test_auth_callback_invalid_json(monkeypatch):
    _patch_auth_callback_deps(monkeypatch)

    async with TestClient(TestServer(_make_app())) as client:
        resp = await client.post(
            "/auth/callback",
            data=b"not json",
            headers={
                "Origin": ALLOWED_ORIGIN,
                "Content-Type": "application/json",
            },
        )
        assert resp.status == 400
        body = await resp.json()
        assert body["error"] == "invalid_json"


@pytest.mark.asyncio
async def test_auth_callback_missing_jwt(monkeypatch):
    _patch_auth_callback_deps(monkeypatch)

    async with TestClient(TestServer(_make_app())) as client:
        resp = await client.post(
            "/auth/callback", json={}, headers={"Origin": ALLOWED_ORIGIN}
        )
        assert resp.status == 400
        assert (await resp.json())["error"] == "missing_jwt"


@pytest.mark.asyncio
async def test_auth_callback_non_string_jwt(monkeypatch):
    _patch_auth_callback_deps(monkeypatch)

    async with TestClient(TestServer(_make_app())) as client:
        resp = await client.post(
            "/auth/callback",
            json={"jwt": 42},
            headers={"Origin": ALLOWED_ORIGIN},
        )
        assert resp.status == 400


@pytest.mark.asyncio
async def test_auth_preflight_allowed_origin():
    async with TestClient(TestServer(_make_app())) as client:
        resp = await client.options(
            "/auth/callback", headers={"Origin": ALLOWED_ORIGIN}
        )
        assert resp.status == 204
        assert resp.headers["Access-Control-Allow-Origin"] == ALLOWED_ORIGIN
        assert resp.headers["Access-Control-Allow-Private-Network"] == "true"
        assert "POST" in resp.headers["Access-Control-Allow-Methods"]


@pytest.mark.asyncio
async def test_auth_preflight_rejects_bad_origin():
    async with TestClient(TestServer(_make_app())) as client:
        resp = await client.options(
            "/auth/callback", headers={"Origin": "https://evil.com"}
        )
        assert resp.status == 403


# -- /ping --


@pytest.mark.asyncio
async def test_loopback_ping_returns_ok():
    async with TestClient(TestServer(_make_app())) as client:
        resp = await client.get("/ping", headers={"Origin": ALLOWED_ORIGIN})
        assert resp.status == 200
        assert (await resp.json()) == {"ok": True}
        assert resp.headers["Access-Control-Allow-Origin"] == ALLOWED_ORIGIN


@pytest.mark.asyncio
async def test_loopback_ping_open_to_any_origin():
    # Intentionally no origin allowlist — the response is a harmless no-op
    # and the PNA consent prompt is not worth protecting here.
    async with TestClient(TestServer(_make_app())) as client:
        resp = await client.get("/ping", headers={"Origin": "https://evil.com"})
        assert resp.status == 200
        assert (await resp.json()) == {"ok": True}


@pytest.mark.asyncio
async def test_loopback_ping_preflight():
    async with TestClient(TestServer(_make_app())) as client:
        resp = await client.options("/ping", headers={"Origin": ALLOWED_ORIGIN})
        assert resp.status == 204
        assert resp.headers["Access-Control-Allow-Private-Network"] == "true"


# -- /api/events --


async def _read_sse_event(resp) -> dict[str, Any]:
    event: dict[str, Any] = {}
    while True:
        line = (await resp.content.readline()).decode().strip()
        if not line:
            return event
        key, _, value = line.partition(": ")
        event[key] = value


@pytest.mark.asyncio
async def test_events_rejects_missing_token():
    async with TestClient(TestServer(_make_app())) as client:
        resp = await client.get("/api/events")
        assert resp.status == 401


@pytest.mark.asyncio
async def test_events_rejects_wrong_token():
    async with TestClient(TestServer(_make_app())) as client:
        resp = await client.get("/api/events?token=wrong")
        assert resp.status == 401


@pytest.mark.asyncio
async def test_events_rejects_non_localhost_host_header():
    server = _make_server()
    async with TestClient(TestServer(_make_app(server))) as client:
        resp = await client.get(
            f"/api/events?token={server.session_token}",
            headers={"Host": "evil.example.com:8766"},
        )
        assert resp.status == 403


@pytest.mark.asyncio
async def test_events_sends_state_on_connect_then_forwards_events(monkeypatch):
    import src.local_server
    from src.event_bus import BrowserSelectionChanged, StateInvalidated, event_bus
    from src.web import dto

    fake_state = {"schemaVersion": 1, "smartFields": []}
    fake_catalog = {"schemaVersion": 1, "chat": {}, "image": {}}
    fake_defaults = MagicMock()
    fake_note_types = [(1, "Basic", ["Front", "Back"])]
    fake_decks = {1: "Default"}
    fake_smart_fields = [MagicMock()]
    fake_account = {"status": "UNAUTHENTICATED", "plan": None, "email": None}
    fake_settings = {"generateAtReview": True}
    build_state = MagicMock(return_value=fake_state)
    monkeypatch.setattr(src.local_server, "_run_on_main_sync", lambda fn: fn())
    monkeypatch.setattr(
        src.local_server.smart_field_service,
        "get_generation_defaults",
        MagicMock(return_value=fake_defaults),
    )
    monkeypatch.setattr(
        src.local_server.smart_field_service,
        "get_all_smart_fields",
        MagicMock(return_value=fake_smart_fields),
    )
    monkeypatch.setattr(
        src.local_server,
        "get_note_types_with_fields",
        MagicMock(return_value=fake_note_types),
    )
    monkeypatch.setattr(
        src.local_server,
        "deck_id_to_name_map",
        MagicMock(return_value=fake_decks),
    )
    monkeypatch.setattr(
        src.local_server,
        "app_state",
        MagicMock(state=fake_account),
    )
    monkeypatch.setattr(dto, "build_state", build_state)
    monkeypatch.setattr(dto, "build_settings", lambda: fake_settings)
    monkeypatch.setattr(dto, "build_catalog", lambda: fake_catalog)
    monkeypatch.setattr(src.local_server, "get_version", lambda: "2.23.9")

    server = _make_server()
    async with TestClient(TestServer(_make_app(server))) as client:
        resp = await client.get(f"/api/events?token={server.session_token}")
        assert resp.status == 200
        assert resp.headers["Content-Type"] == "text/event-stream"

        # The snapshot is the head of the stream.
        event = await _read_sse_event(resp)
        assert event["event"] == "state"
        assert json.loads(event["data"]) == fake_state

        build_state.assert_called_with(
            defaults=fake_defaults,
            note_types=fake_note_types,
            decks=fake_decks,
            smart_fields=fake_smart_fields,
            account=fake_account,
            settings=fake_settings,
            app_version="2.23.9",
        )

        event = await _read_sse_event(resp)
        assert event["event"] == "catalog"
        assert json.loads(event["data"]) == fake_catalog

        # Ephemeral events are forwarded with their payload.
        event_bus.publish(BrowserSelectionChanged({"note": None, "count": 2}))
        event = await _read_sse_event(resp)
        assert event["event"] == "anki.browserSelectionChanged"
        assert json.loads(event["data"]) == {"note": None, "count": 2}

        # Invalidation triggers a fresh whole-state push.
        event_bus.publish(StateInvalidated())
        event = await _read_sse_event(resp)
        assert event["event"] == "state"
        assert json.loads(event["data"]) == fake_state


# -- /api/command --


def _patch_command_route_deps(monkeypatch):
    import src.local_server

    fake_service = MagicMock()
    fake_dto = MagicMock()
    monkeypatch.setattr(src.local_server, "smart_field_service", fake_service)
    monkeypatch.setattr(src.local_server, "dto", fake_dto)
    monkeypatch.setattr(src.local_server, "_run_on_main_sync", lambda fn: fn())
    return fake_service, fake_dto


def _command_request(command: str, payload: dict[str, Any]) -> dict[str, Any]:
    return {"command": command, "payload": payload}


@pytest.mark.asyncio
async def test_command_rejects_missing_token():
    async with TestClient(TestServer(_make_app())) as client:
        resp = await client.post("/api/command", json={})
        assert resp.status == 401


@pytest.mark.asyncio
async def test_command_rejects_unknown_command_and_lists_valid_ones(monkeypatch):
    _patch_command_route_deps(monkeypatch)

    server = _make_server()
    async with TestClient(TestServer(_make_app(server))) as client:
        resp = await client.post(
            "/api/command",
            json=_command_request("smartFields.save", {}),
            headers={"X-Session-Token": server.session_token},
        )
        assert resp.status == 400
        error = (await resp.json())["error"]
        assert "Unknown command: smartFields.save" in error
        assert "smartFields.create" in error
        assert "smartFields.update" in error
        assert "smartFields.delete" in error
        assert "defaults.save" in error
        assert "defaults.chat.save" in error
        assert "prompts.test" in error


@pytest.mark.asyncio
async def test_create_smart_field_command_dispatch(monkeypatch):
    fake_service, fake_dto = _patch_command_route_deps(monkeypatch)
    parsed = object()
    fake_dto.parse_smart_field_create.return_value = parsed

    server = _make_server()
    async with TestClient(TestServer(_make_app(server))) as client:
        resp = await client.post(
            "/api/command",
            json=_command_request("smartFields.create", {"any": "payload"}),
            headers={"X-Session-Token": server.session_token},
        )
        assert resp.status == 200
        assert (await resp.json()) == {"ok": True}
        fake_dto.parse_smart_field_create.assert_called_once_with({"any": "payload"})
        fake_service.create_smart_field.assert_called_once_with(parsed)


@pytest.mark.asyncio
async def test_update_smart_field_command_dispatch(monkeypatch):
    fake_service, fake_dto = _patch_command_route_deps(monkeypatch)
    parsed = object()
    fake_dto.parse_smart_field_update.return_value = parsed

    server = _make_server()
    async with TestClient(TestServer(_make_app(server))) as client:
        resp = await client.post(
            "/api/command",
            json=_command_request(
                "smartFields.update", {"id": "existing-smart-field-id"}
            ),
            headers={"X-Session-Token": server.session_token},
        )
        assert resp.status == 200
        assert (await resp.json()) == {"ok": True}
        fake_dto.parse_smart_field_update.assert_called_once_with(
            {"id": "existing-smart-field-id"}
        )
        fake_service.update_smart_field.assert_called_once_with(parsed)


@pytest.mark.asyncio
async def test_command_returns_400_on_validation_error(monkeypatch):
    fake_service, fake_dto = _patch_command_route_deps(monkeypatch)
    fake_dto.parse_smart_field_create.side_effect = ValueError("Missing promptText")

    server = _make_server()
    async with TestClient(TestServer(_make_app(server))) as client:
        resp = await client.post(
            "/api/command",
            json=_command_request("smartFields.create", {}),
            headers={"X-Session-Token": server.session_token},
        )
        assert resp.status == 400
        assert (await resp.json()) == {"ok": False, "error": "Missing promptText"}
        fake_service.create_smart_field.assert_not_called()


@pytest.mark.asyncio
async def test_delete_smart_field_command_dispatch(monkeypatch):
    fake_service, fake_dto = _patch_command_route_deps(monkeypatch)
    fake_dto.parse_smart_field_id.return_value = "existing-smart-field-id"

    server = _make_server()
    async with TestClient(TestServer(_make_app(server))) as client:
        resp = await client.post(
            "/api/command",
            json=_command_request(
                "smartFields.delete",
                {"id": "existing-smart-field-id"},
            ),
            headers={"X-Session-Token": server.session_token},
        )
        assert resp.status == 200
        fake_dto.parse_smart_field_id.assert_called_once_with(
            {"id": "existing-smart-field-id"}
        )
        fake_service.delete_smart_field.assert_called_once_with(
            "existing-smart-field-id"
        )


@pytest.mark.asyncio
async def test_save_defaults_command_dispatch(monkeypatch):
    fake_service, fake_dto = _patch_command_route_deps(monkeypatch)
    parsed = MagicMock()
    fake_dto.parse_generation_defaults.return_value = parsed

    server = _make_server()
    async with TestClient(TestServer(_make_app(server))) as client:
        resp = await client.post(
            "/api/command",
            json=_command_request(
                "defaults.save", {"chat": {}, "tts": {}, "image": {}}
            ),
            headers={"X-Session-Token": server.session_token},
        )
        assert resp.status == 200
        fake_service.save_chat_defaults.assert_called_once_with(parsed.chat)
        fake_service.save_tts_defaults.assert_called_once_with(parsed.tts)
        fake_service.save_image_defaults.assert_called_once_with(parsed.image)


@pytest.mark.asyncio
async def test_save_chat_defaults_only_updates_chat(monkeypatch):
    fake_service, fake_dto = _patch_command_route_deps(monkeypatch)
    parsed = MagicMock()
    fake_dto.parse_chat_generation_settings.return_value = parsed

    server = _make_server()
    async with TestClient(TestServer(_make_app(server))) as client:
        resp = await client.post(
            "/api/command",
            json=_command_request("defaults.chat.save", {"provider": "auto"}),
            headers={"X-Session-Token": server.session_token},
        )

        assert resp.status == 200
        fake_service.save_chat_defaults.assert_called_once_with(parsed)
        fake_service.save_tts_defaults.assert_not_called()
        fake_service.save_image_defaults.assert_not_called()


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("command", "parser", "service_method"),
    [
        (
            "defaults.image.save",
            "parse_image_generation_settings",
            "save_image_defaults",
        ),
        ("defaults.tts.save", "parse_tts_generation_settings", "save_tts_defaults"),
    ],
)
async def test_modality_default_commands_only_update_their_setting(
    monkeypatch, command, parser, service_method
):
    fake_service, fake_dto = _patch_command_route_deps(monkeypatch)
    parsed = object()
    getattr(fake_dto, parser).return_value = parsed

    server = _make_server()
    async with TestClient(TestServer(_make_app(server))) as client:
        resp = await client.post(
            "/api/command",
            json=_command_request(command, {"provider": "provider"}),
            headers={"X-Session-Token": server.session_token},
        )

        assert resp.status == 200
        getattr(fake_service, service_method).assert_called_once_with(parsed)


@pytest.mark.asyncio
async def test_save_settings_command_dispatch(monkeypatch):
    import src.local_server

    _, fake_dto = _patch_command_route_deps(monkeypatch)
    parsed = object()
    fake_dto.parse_settings.return_value = parsed
    save_settings = MagicMock()
    monkeypatch.setattr(
        src.local_server.settings_service, "save_settings", save_settings
    )

    server = _make_server()
    async with TestClient(TestServer(_make_app(server))) as client:
        resp = await client.post(
            "/api/command",
            json=_command_request("settings.save", {"generateAtReview": True}),
            headers={"X-Session-Token": server.session_token},
        )

        assert resp.status == 200
        assert (await resp.json()) == {"ok": True}
        fake_dto.parse_settings.assert_called_once_with({"generateAtReview": True})
        save_settings.assert_called_once_with(parsed)


@pytest.mark.asyncio
async def test_prompt_test_command_returns_ephemeral_result(monkeypatch):
    import src.local_server

    request = object()
    context = object()
    monkeypatch.setattr(
        src.local_server.dto, "parse_text_prompt_test", lambda _: request
    )
    monkeypatch.setattr(
        src.local_server, "prepare_text_prompt_test", lambda parsed: context
    )

    async def run_text_prompt_test(prepared):
        assert prepared is context
        return {"text": "A domesticated canine"}

    monkeypatch.setattr(src.local_server, "run_text_prompt_test", run_text_prompt_test)
    monkeypatch.setattr(src.local_server, "_run_on_main_sync", lambda fn: fn())

    server = _make_server()
    async with TestClient(TestServer(_make_app(server))) as client:
        resp = await client.post(
            "/api/command",
            json=_command_request("prompts.test", {"cardId": 99}),
            headers={"X-Session-Token": server.session_token},
        )

        assert resp.status == 200
        assert (await resp.json()) == {
            "ok": True,
            "result": {"text": "A domesticated canine"},
        }


@pytest.mark.asyncio
async def test_prompt_generate_command_prepares_names_and_returns_prompt(monkeypatch):
    import src.local_server
    from src.web.dto import PromptGenerateRequest

    request = PromptGenerateRequest(
        note_type_id=123,
        deck_id=1,
        target_field_name="Back",
        field_type="chat",
        generation_prompt="Write a concise definition",
    )
    monkeypatch.setattr(
        src.local_server.dto, "parse_prompt_generate", lambda _: request
    )
    monkeypatch.setattr(
        src.local_server,
        "get_note_types_with_fields",
        lambda: [(123, "Basic", ["Front", "Back"])],
    )
    monkeypatch.setattr(src.local_server, "deck_id_to_name_map", lambda: {1: "Default"})
    monkeypatch.setattr(src.local_server, "_run_on_main_sync", lambda fn: fn())
    response = MagicMock()
    response.json = AsyncMock(return_value={"prompt": "Define {{Front}}"})
    get_api_response = AsyncMock(return_value=response)
    monkeypatch.setattr(
        src.local_server, "api", MagicMock(get_api_response=get_api_response)
    )

    server = _make_server()
    async with TestClient(TestServer(_make_app(server))) as client:
        resp = await client.post(
            "/api/command",
            json=_command_request("prompts.generate", {"noteTypeId": 123}),
            headers={"X-Session-Token": server.session_token},
        )

        assert resp.status == 200
        assert (await resp.json()) == {
            "ok": True,
            "result": {"prompt": "Define {{Front}}"},
        }
        get_api_response.assert_awaited_once_with(
            path="prompt/generate",
            args={
                "note_type": "Basic",
                "deck_name": "Default",
                "target_field": "Back",
                "field_type": "chat",
                "fields": ["Front", "Back"],
                "generation_prompt": "Write a concise definition",
            },
            timeout_sec=30,
        )


@pytest.mark.asyncio
async def test_send_feedback_command_posts_plugin_context(monkeypatch):
    import src.local_server

    monkeypatch.setattr(
        src.local_server.dto,
        "parse_feedback_message",
        lambda _: "Please add a shortcut",
    )
    monkeypatch.setattr(src.local_server, "config", MagicMock(auth_token="signed-in"))
    monkeypatch.setattr(src.local_server, "get_version", lambda: "2.23.9")
    monkeypatch.setattr(src.local_server, "_run_on_main_sync", lambda fn: fn())
    get_api_response = AsyncMock(return_value=MagicMock())
    monkeypatch.setattr(
        src.local_server, "api", MagicMock(get_api_response=get_api_response)
    )

    server = _make_server()
    async with TestClient(TestServer(_make_app(server))) as client:
        resp = await client.post(
            "/api/command",
            json=_command_request("support.sendFeedback", {"message": "anything"}),
            headers={"X-Session-Token": server.session_token},
        )

        assert resp.status == 200
        assert (await resp.json()) == {"ok": True}
        get_api_response.assert_awaited_once_with(
            path="feedback",
            args={
                "message": "Please add a shortcut",
                "version": "2.23.9",
                "platform": src.local_server.sys.platform,
            },
        )


@pytest.mark.asyncio
async def test_send_feedback_command_requires_authentication(monkeypatch):
    import src.local_server

    monkeypatch.setattr(
        src.local_server.dto, "parse_feedback_message", lambda _: "Please help"
    )
    monkeypatch.setattr(src.local_server, "config", MagicMock(auth_token=None))
    monkeypatch.setattr(src.local_server, "_run_on_main_sync", lambda fn: fn())
    get_api_response = AsyncMock()
    monkeypatch.setattr(
        src.local_server, "api", MagicMock(get_api_response=get_api_response)
    )

    server = _make_server()
    async with TestClient(TestServer(_make_app(server))) as client:
        resp = await client.post(
            "/api/command",
            json=_command_request("support.sendFeedback", {"message": "Please help"}),
            headers={"X-Session-Token": server.session_token},
        )

        assert resp.status == 400
        assert (await resp.json()) == {
            "ok": False,
            "error": "You must be signed in to send feedback",
        }
        get_api_response.assert_not_awaited()


@pytest.mark.asyncio
async def test_logout_command_clears_auth_and_refreshes_state(monkeypatch):
    import src.local_server

    logout = MagicMock()
    parse_auth_logout = MagicMock()
    monkeypatch.setattr(src.local_server.auth_service, "logout", logout)
    monkeypatch.setattr(src.local_server.dto, "parse_auth_logout", parse_auth_logout)
    monkeypatch.setattr(src.local_server, "_run_on_main_sync", lambda fn: fn())

    server = _make_server()
    async with TestClient(TestServer(_make_app(server))) as client:
        resp = await client.post(
            "/api/command",
            json=_command_request("auth.logout", {}),
            headers={"X-Session-Token": server.session_token},
        )

        assert resp.status == 200
        assert (await resp.json()) == {"ok": True}
        parse_auth_logout.assert_called_once_with({})
        logout.assert_called_once_with()


@pytest.mark.asyncio
async def test_refresh_account_command_fetches_account_state(monkeypatch):
    import src.local_server

    refresh_account = MagicMock()
    parse_account_refresh = MagicMock()
    monkeypatch.setattr(
        src.local_server.auth_service, "refresh_account", refresh_account
    )
    monkeypatch.setattr(
        src.local_server.dto, "parse_account_refresh", parse_account_refresh
    )
    monkeypatch.setattr(src.local_server, "_run_on_main_sync", lambda fn: fn())

    server = _make_server()
    async with TestClient(TestServer(_make_app(server))) as client:
        resp = await client.post(
            "/api/command",
            json=_command_request("account.refresh", {}),
            headers={"X-Session-Token": server.session_token},
        )

        assert resp.status == 200
        assert (await resp.json()) == {"ok": True}
        parse_account_refresh.assert_called_once_with({})
        refresh_account.assert_called_once_with()


@pytest.mark.asyncio
async def test_image_test_command_returns_ephemeral_result(monkeypatch):
    import src.local_server

    request = object()
    context = object()
    monkeypatch.setattr(
        src.local_server.dto, "parse_image_prompt_test", lambda _: request
    )
    monkeypatch.setattr(
        src.local_server, "prepare_image_prompt_test", lambda parsed: context
    )

    async def run_image_prompt_test(prepared):
        assert prepared is context
        return {"dataUrl": "data:image/png;base64,aW1hZ2U="}

    monkeypatch.setattr(
        src.local_server, "run_image_prompt_test", run_image_prompt_test
    )
    monkeypatch.setattr(src.local_server, "_run_on_main_sync", lambda fn: fn())

    server = _make_server()
    async with TestClient(TestServer(_make_app(server))) as client:
        resp = await client.post(
            "/api/command",
            json=_command_request("images.test", {"cardId": 99}),
            headers={"X-Session-Token": server.session_token},
        )

        assert resp.status == 200
        assert (await resp.json())["result"]["dataUrl"].startswith("data:image/")


@pytest.mark.asyncio
async def test_save_test_result_command_dispatch(monkeypatch):
    import src.local_server

    parsed = object()
    monkeypatch.setattr(
        src.local_server.dto, "parse_save_test_result", lambda _: parsed
    )
    save_test_result = MagicMock()
    monkeypatch.setattr(src.local_server, "save_test_result", save_test_result)
    monkeypatch.setattr(src.local_server, "_run_on_main_sync", lambda fn: fn())

    server = _make_server()
    async with TestClient(TestServer(_make_app(server))) as client:
        resp = await client.post(
            "/api/command",
            json=_command_request(
                "notes.saveTestResult",
                {"token": "token-1", "cardId": 99, "fieldName": "Back"},
            ),
            headers={"X-Session-Token": server.session_token},
        )

        assert resp.status == 200
        assert (await resp.json()) == {"ok": True}
        save_test_result.assert_called_once_with(parsed)


@pytest.mark.asyncio
async def test_save_test_result_command_surfaces_an_expired_result(monkeypatch):
    import src.local_server
    from src.services.prompt_test_service import EXPIRED_TEST_RESULT_MESSAGE

    monkeypatch.setattr(
        src.local_server.dto, "parse_save_test_result", lambda _: object()
    )

    def expired(_):
        raise ValueError(EXPIRED_TEST_RESULT_MESSAGE)

    monkeypatch.setattr(src.local_server, "save_test_result", expired)
    monkeypatch.setattr(src.local_server, "_run_on_main_sync", lambda fn: fn())

    server = _make_server()
    async with TestClient(TestServer(_make_app(server))) as client:
        resp = await client.post(
            "/api/command",
            json=_command_request("notes.saveTestResult", {"token": "stale"}),
            headers={"X-Session-Token": server.session_token},
        )

        assert resp.status == 400
        assert (await resp.json()) == {
            "ok": False,
            "error": EXPIRED_TEST_RESULT_MESSAGE,
        }


@pytest.mark.asyncio
async def test_voice_catalog_is_available_without_api_token(monkeypatch):
    import src.local_server

    monkeypatch.setattr(
        src.local_server.dto,
        "build_voice_catalog",
        lambda: {"schemaVersion": 1, "voices": [{"name": "Alloy"}]},
    )

    async with TestClient(TestServer(_make_app())) as client:
        resp = await client.get("/app/voice-catalog.json")

        assert resp.status == 200
        assert (await resp.json())["voices"] == [{"name": "Alloy"}]


@pytest.mark.asyncio
async def test_open_browser_command_dispatch(monkeypatch):
    import src.local_server

    _, fake_dto = _patch_command_route_deps(monkeypatch)
    open_anki_browser = MagicMock()
    monkeypatch.setattr(src.local_server, "open_anki_browser", open_anki_browser)

    server = _make_server()
    async with TestClient(TestServer(_make_app(server))) as client:
        resp = await client.post(
            "/api/command",
            json=_command_request("ui.openBrowser", {}),
            headers={"X-Session-Token": server.session_token},
        )

        assert resp.status == 200
        assert (await resp.json()) == {"ok": True}
        fake_dto.parse_ui_open_browser.assert_called_once_with({})
        open_anki_browser.assert_called_once_with()
