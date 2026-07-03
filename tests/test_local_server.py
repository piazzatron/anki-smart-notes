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

from typing import Any
from unittest.mock import MagicMock

import pytest
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer

from src.models import (
    ChatGenerationSettings,
    ImageGenerationSettings,
    TTSGenerationSettings,
)
from src.models.smart_fields import ChatSmartFieldSettings


def _ok(result: Any) -> dict[str, Any]:
    return {"result": result, "error": None}


def _err(message: str) -> dict[str, Any]:
    return {"result": None, "error": message}


def _make_server():
    from src.local_server import LocalServer

    processor = MagicMock()
    return LocalServer(processor)


def _make_app():
    server = _make_server()
    app = web.Application()
    app.router.add_post("/", server._handle_request)
    app.router.add_post("/auth/callback", server._handle_auth_callback)
    app.router.add_options("/auth/callback", server._handle_auth_preflight)
    app.router.add_get("/ping", server._handle_loopback_ping)
    app.router.add_options("/ping", server._handle_ping_preflight)
    return app


ALLOWED_ORIGIN = "https://smart-notes.xyz"


def make_request(action: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
    req: dict[str, Any] = {"action": action, "version": 1}
    if params is not None:
        req["params"] = params
    return req


async def _post(client: TestClient, data: dict[str, Any]) -> dict[str, Any]:
    resp = await client.post("/", json=data)
    return await resp.json()


@pytest.mark.asyncio
async def test_ping():
    async with TestClient(TestServer(_make_app())) as client:
        data = await _post(client, make_request("ping"))
        assert data == _ok("pong")


@pytest.mark.asyncio
async def test_invalid_json():
    async with TestClient(TestServer(_make_app())) as client:
        resp = await client.post(
            "/", data=b"not json", headers={"Content-Type": "application/json"}
        )
        data = await resp.json()
        assert data["error"] is not None


@pytest.mark.asyncio
async def test_bad_version():
    async with TestClient(TestServer(_make_app())) as client:
        data = await _post(client, {"action": "ping", "version": 99})
        assert data == _err("Unsupported version: 99, expected 1")


@pytest.mark.asyncio
async def test_unknown_action():
    async with TestClient(TestServer(_make_app())) as client:
        data = await _post(client, make_request("nonExistent"))
        assert data == _err("Unknown action: nonExistent")


@pytest.mark.asyncio
async def test_client_facing_error_logs_below_error(monkeypatch):
    import src.local_server
    from src.api_client import ClientFacingAPIError

    server = _make_server()
    error_logs = []
    info_logs = []

    async def raise_client_facing_error(_params):
        raise ClientFacingAPIError("Try rewording the image prompt.")

    server._actions["clientFacing"] = raise_client_facing_error
    app = web.Application()
    app.router.add_post("/", server._handle_request)

    monkeypatch.setattr(
        src.local_server.logger,
        "error",
        lambda *args, **kwargs: error_logs.append(args),
    )
    monkeypatch.setattr(
        src.local_server.logger, "info", lambda *args, **kwargs: info_logs.append(args)
    )

    async with TestClient(TestServer(app)) as client:
        data = await _post(client, make_request("clientFacing", {}))

    assert data == _err("Try rewording the image prompt.")
    assert error_logs == []
    assert info_logs == [
        (
            "Local server client-facing error handling clientFacing: Try rewording the image prompt.",
        )
    ]


@pytest.mark.asyncio
async def test_get_smart_fields_missing_note_type():
    async with TestClient(TestServer(_make_app())) as client:
        data = await _post(client, make_request("getSmartFields", {}))
        assert data == _err("noteType is required")


@pytest.mark.asyncio
async def test_get_smart_fields(monkeypatch):
    import src.local_server

    monkeypatch.setattr(
        src.local_server,
        "get_prompts_for_note",
        lambda note_type, deck_id, fallback_to_global_deck=True: {"Field1": "prompt1"},
    )
    monkeypatch.setattr(
        src.local_server,
        "get_extras",
        lambda note_type, field, deck_id: {"type": "chat", "automatic": True},
    )

    async with TestClient(TestServer(_make_app())) as client:
        data = await _post(
            client, make_request("getSmartFields", {"noteType": "Basic"})
        )
        assert data["error"] is None
        assert data["result"]["Field1"]["prompt"] == "prompt1"
        assert data["result"]["Field1"]["extras"]["type"] == "chat"


@pytest.mark.asyncio
async def test_get_smart_fields_empty(monkeypatch):
    import src.local_server

    monkeypatch.setattr(
        src.local_server,
        "get_prompts_for_note",
        lambda note_type, deck_id, fallback_to_global_deck=True: None,
    )

    async with TestClient(TestServer(_make_app())) as client:
        data = await _post(
            client, make_request("getSmartFields", {"noteType": "Basic"})
        )
        assert data == _ok({})


@pytest.mark.asyncio
async def test_add_smart_field_missing_params():
    async with TestClient(TestServer(_make_app())) as client:
        data = await _post(client, make_request("addSmartField", {"noteType": "Basic"}))
        assert data["error"] == "noteType, field, and prompt are required"


@pytest.mark.asyncio
async def test_add_smart_field_already_exists(monkeypatch):
    import src.local_server

    monkeypatch.setattr(
        src.local_server,
        "get_prompts_for_note",
        lambda note_type, deck_id, fallback_to_global_deck=False: {"Back": "existing"},
    )

    async with TestClient(TestServer(_make_app())) as client:
        data = await _post(
            client,
            make_request(
                "addSmartField",
                {"noteType": "Basic", "field": "Back", "prompt": "test"},
            ),
        )
        assert "already exists" in data["error"]


@pytest.mark.asyncio
async def test_add_smart_field_success(monkeypatch):
    import src.local_server

    monkeypatch.setattr(
        src.local_server,
        "get_prompts_for_note",
        lambda note_type, deck_id, fallback_to_global_deck=False: None,
    )
    smart_field_service = _fake_smart_field_service()
    monkeypatch.setattr(src.local_server, "smart_field_service", smart_field_service)
    monkeypatch.setattr(src.local_server, "get_note_type_id_from_name", lambda _: 123)
    monkeypatch.setattr(src.local_server, "_run_on_main_sync", lambda fn: fn())

    async with TestClient(TestServer(_make_app())) as client:
        data = await _post(
            client,
            make_request(
                "addSmartField",
                {
                    "noteType": "Basic",
                    "field": "Back",
                    "prompt": "Define {{Front}}",
                },
            ),
        )
        assert data == _ok(True)
        smart_field_service.save_smart_field.assert_called_once()
        (saved_field,) = smart_field_service.save_smart_field.call_args.args
        assert smart_field_service.save_smart_field.call_args.kwargs == {}
        assert isinstance(saved_field.settings, ChatSmartFieldSettings)
        assert saved_field.settings.uses_default_generation_settings is True


@pytest.mark.asyncio
async def test_add_smart_field_with_custom_reasoning_level(monkeypatch):
    import src.local_server

    monkeypatch.setattr(
        src.local_server,
        "get_prompts_for_note",
        lambda note_type, deck_id, fallback_to_global_deck=False: None,
    )
    smart_field_service = _fake_smart_field_service()
    monkeypatch.setattr(src.local_server, "smart_field_service", smart_field_service)
    monkeypatch.setattr(src.local_server, "get_note_type_id_from_name", lambda _: 123)
    monkeypatch.setattr(src.local_server, "_run_on_main_sync", lambda fn: fn())

    async with TestClient(TestServer(_make_app())) as client:
        data = await _post(
            client,
            make_request(
                "addSmartField",
                {
                    "noteType": "Basic",
                    "field": "Back",
                    "prompt": "Define {{Front}}",
                    "useCustomModel": True,
                    "chatOptions": {
                        "provider": "auto",
                        "model": "auto",
                        "reasoningLevel": "high",
                        "webSearch": False,
                    },
                },
            ),
        )
        assert data == _ok(True)
        (saved_field,) = smart_field_service.save_smart_field.call_args.args
        assert smart_field_service.save_smart_field.call_args.kwargs == {}
        assert isinstance(saved_field.settings, ChatSmartFieldSettings)
        assert saved_field.settings.reasoning_level == "high"
        assert saved_field.settings.uses_default_generation_settings is False


@pytest.mark.asyncio
async def test_update_smart_field_not_exists(monkeypatch):
    import src.local_server

    monkeypatch.setattr(
        src.local_server,
        "get_prompts_for_note",
        lambda note_type, deck_id, fallback_to_global_deck=False: None,
    )

    async with TestClient(TestServer(_make_app())) as client:
        data = await _post(
            client,
            make_request(
                "updateSmartField",
                {"noteType": "Basic", "field": "Back", "prompt": "test"},
            ),
        )
        assert "does not exist" in data["error"]


@pytest.mark.asyncio
async def test_update_smart_field_success(monkeypatch):
    import src.local_server

    monkeypatch.setattr(
        src.local_server,
        "get_prompts_for_note",
        lambda note_type, deck_id, fallback_to_global_deck=False: {
            "Back": "old prompt"
        },
    )
    smart_field_service = _fake_smart_field_service()
    monkeypatch.setattr(src.local_server, "smart_field_service", smart_field_service)
    monkeypatch.setattr(src.local_server, "get_note_type_id_from_name", lambda _: 123)
    monkeypatch.setattr(src.local_server, "_run_on_main_sync", lambda fn: fn())

    async with TestClient(TestServer(_make_app())) as client:
        data = await _post(
            client,
            make_request(
                "updateSmartField",
                {
                    "noteType": "Basic",
                    "field": "Back",
                    "prompt": "New prompt {{Front}}",
                },
            ),
        )
        assert data == _ok(True)
        smart_field_service.save_smart_field.assert_called_once()


def _fake_smart_field_service() -> MagicMock:
    service = MagicMock()
    service.get_chat_defaults.return_value = ChatGenerationSettings(
        provider="auto",
        model="auto",
        reasoning_level="off",
        web_search_enabled=False,
    )
    service.get_tts_defaults.return_value = TTSGenerationSettings(
        provider="openai",
        model="tts-1",
        voice_id="alloy",
    )
    service.get_image_defaults.return_value = ImageGenerationSettings(
        provider="openai",
        model="gpt-image-1.5-low",
    )
    return service


@pytest.mark.asyncio
async def test_remove_smart_field_missing_params():
    async with TestClient(TestServer(_make_app())) as client:
        data = await _post(
            client, make_request("removeSmartField", {"noteType": "Basic"})
        )
        assert data["error"] == "noteType and field are required"


@pytest.mark.asyncio
async def test_remove_smart_field_success(monkeypatch):
    import src.local_server

    smart_field_service = MagicMock()
    monkeypatch.setattr(src.local_server, "smart_field_service", smart_field_service)
    monkeypatch.setattr(src.local_server, "get_note_type_id_from_name", lambda _: 123)
    monkeypatch.setattr(src.local_server, "_run_on_main_sync", lambda fn: fn())

    async with TestClient(TestServer(_make_app())) as client:
        data = await _post(
            client,
            make_request(
                "removeSmartField",
                {"noteType": "Basic", "field": "Back"},
            ),
        )
        assert data == _ok(True)
        smart_field_service.delete_smart_field.assert_called_once_with(123, -1, "Back")


@pytest.mark.asyncio
async def test_generate_note_missing_note_id():
    async with TestClient(TestServer(_make_app())) as client:
        data = await _post(client, make_request("generateNote", {}))
        assert data["error"] == "noteId is required"


@pytest.mark.asyncio
async def test_generate_note_no_collection(monkeypatch):
    import src.local_server

    monkeypatch.setattr(src.local_server, "mw", None)

    async with TestClient(TestServer(_make_app())) as client:
        data = await _post(client, make_request("generateNote", {"noteId": 1}))
        assert data["error"] == "Anki collection not available"


@pytest.mark.asyncio
async def test_generate_notes_missing_note_ids():
    async with TestClient(TestServer(_make_app())) as client:
        data = await _post(client, make_request("generateNotes", {}))
        assert data["error"] == "noteIds is required"


@pytest.mark.asyncio
async def test_ui_custom_image_prompt_missing_params():
    async with TestClient(TestServer(_make_app())) as client:
        data = await _post(client, make_request("uiCustomImagePrompt", {}))
        assert data == _err("noteId and field are required")


@pytest.mark.asyncio
async def test_ui_custom_image_prompt_no_collection(monkeypatch):
    import src.local_server

    monkeypatch.setattr(src.local_server, "mw", None)

    async with TestClient(TestServer(_make_app())) as client:
        data = await _post(
            client, make_request("uiCustomImagePrompt", {"noteId": 1, "field": "Back"})
        )
        assert data == _err("Anki collection not available")


@pytest.mark.asyncio
async def test_ui_custom_image_prompt_opens_dialog(monkeypatch):
    import src.local_server

    class FakeCard:
        did = 123

    class FakeNote:
        def __init__(self) -> None:
            self.updated_fields: dict[str, str] = {}

        def keys(self):
            return ["Front", "Back"]

        def cards(self):
            return [FakeCard()]

        def __setitem__(self, field: str, value: str) -> None:
            self.updated_fields[field] = value

    class FakeCollection:
        def __init__(self, note: FakeNote) -> None:
            self.note = note
            self.updated_notes = []

        def get_note(self, note_id):
            assert note_id == 42
            return self.note

        def update_note(self, note):
            self.updated_notes.append(note)

    class FakeSignal:
        def connect(self, _callback):
            return None

    class FakeCustomImagePrompt:
        def __init__(self, **kwargs) -> None:
            opened_dialogs.append(self)
            self.kwargs = kwargs
            self.finished = FakeSignal()
            self.did_show = False

        def show(self) -> None:
            self.did_show = True

    note = FakeNote()
    fake_mw = MagicMock()
    fake_mw.col = FakeCollection(note)
    opened_dialogs = []

    monkeypatch.setattr(src.local_server, "mw", fake_mw)
    monkeypatch.setattr(src.local_server, "CustomImagePrompt", FakeCustomImagePrompt)
    monkeypatch.setattr(src.local_server, "_run_on_main_sync", lambda fn: fn())

    async with TestClient(TestServer(_make_app())) as client:
        data = await _post(
            client,
            make_request("uiCustomImagePrompt", {"noteId": 42, "field": "Back"}),
        )

    assert data == _ok(True)
    assert len(opened_dialogs) == 1
    assert opened_dialogs[0].did_show is True
    assert opened_dialogs[0].kwargs["note"] is note
    assert opened_dialogs[0].kwargs["deck_id"] == 123
    assert opened_dialogs[0].kwargs["field_upper"] == "Back"
    assert opened_dialogs[0].kwargs["parent"] is fake_mw

    opened_dialogs[0].kwargs["on_success"]("image.webp")

    assert note.updated_fields == {"Back": "image.webp"}
    assert fake_mw.col.updated_notes == [note]


@pytest.mark.asyncio
async def test_generate_notes_no_collection(monkeypatch):
    import src.local_server

    monkeypatch.setattr(src.local_server, "mw", None)

    async with TestClient(TestServer(_make_app())) as client:
        data = await _post(client, make_request("generateNotes", {"noteIds": [1, 2]}))
        assert data["error"] == "Anki collection not available"


@pytest.mark.asyncio
async def test_generate_notes_returns_batch_failures(monkeypatch):
    import src.local_server

    class FakeCard:
        did = 123

    class FakeNote:
        def __init__(self, note_id: int) -> None:
            self.id = note_id

        def cards(self):
            return [FakeCard()]

    updated_note = FakeNote(1)
    failed_note = FakeNote(2)
    skipped_note = FakeNote(3)
    collection = MagicMock()
    collection.get_note.side_effect = lambda note_id: FakeNote(note_id)
    fake_mw = MagicMock()
    fake_mw.col = collection
    monkeypatch.setattr(src.local_server, "mw", fake_mw)
    monkeypatch.setattr(src.local_server, "_run_on_main_sync", lambda fn: fn())

    server = _make_server()

    async def process_batch(note_ids, *, overwrite_fields, did_map):
        assert note_ids == [1, 2, 3]
        assert overwrite_fields is True
        assert did_map == {1: 123, 2: 123, 3: 123}
        return [updated_note], [failed_note], [skipped_note], False

    server._processor._process_notes_batch = process_batch
    app = web.Application()
    app.router.add_post("/", server._handle_request)

    async with TestClient(TestServer(app)) as client:
        data = await _post(
            client,
            make_request(
                "generateNotes",
                {"noteIds": [1, 2, 3], "overwrite": True},
            ),
        )

    assert data == _ok({"updated": [1], "failed": [2], "skipped": [3]})
    collection.update_notes.assert_called_once_with([updated_note])


# -- /auth/callback --


def _patch_auth_callback_deps(monkeypatch):
    """Replace config/sentry/app_state so _handle_auth_callback is pure."""
    import src.local_server

    written: dict[str, Any] = {"jwt": None}

    class FakeConfig:
        auth_token = None

    fake_config = FakeConfig()

    def fake_run_on_main(fn):
        fn()
        written["jwt"] = fake_config.auth_token

    fake_mw = MagicMock()
    fake_mw.taskman.run_on_main = fake_run_on_main
    monkeypatch.setattr(src.local_server, "config", fake_config)
    monkeypatch.setattr(src.local_server, "mw", fake_mw)
    monkeypatch.setattr(src.local_server, "sentry", None)
    monkeypatch.setattr(src.local_server, "app_state", MagicMock())
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
