# Architecture

Smart Notes is a fully typed Python 3 Anki add-on with a React web UI. The add-on hooks into Anki, stores Smart Field configuration in its own SQLite database, and calls the Smart Notes server for every chat, text-to-speech and image generation. A local HTTP server inside the add-on serves the web UI to an embedded Qt webview.

## Entry point and startup

- **`__init__.py`** → **`src/main.py`**: creates the `NoteProcessor` and calls `setup_hooks()`.
- **`src/hooks.py`**: Anki hooks, menus, the editor button, and the startup and profile lifecycle (migrations, the local server, background evaluators).

## Generation

- **`src/note_proccessor.py`** (`NoteProcessor`): generates a note's Smart Fields in dependency order. It has entry points for a batch, a single card and a single field.
- **`src/dag.py`** / **`src/nodes.py`**: the dependency graph between Smart Fields that reference other fields. `SmartFieldService` rejects a cycle when a Smart Field is saved, and `NoteProcessor` stops rather than spinning if one reaches the database anyway.
- **`src/field_resolver.py`**: generates one field by its type (chat, TTS or image) and writes any media.
- **`src/prompt_fields.py`** / **`src/prompt_helpers.py`**: extract `{{field}}` references and interpolate them.
- **`src/review_time_evaluator.py`** / **`src/add_time_evaluator.py`**: generate in the background during review and after notes are added.
- **`src/chat_provider.py`**, **`src/tts_provider.py`**, **`src/image_provider.py`** → **`src/api_client.py`**: calls to the Smart Notes server. **`src/open_ai_client.py`** is the legacy bring-your-own-key path.

## State, persistence and configuration

- **`src/services/`**: `smart_field_service.py` (Smart Fields and generation defaults, in SQLite), `settings_service.py`, `prompt_test_service.py` and `auth_service.py`.
- **`src/database/`**: the SQLite connection and migrations. The header of `migrations.py` explains their order.
- **`src/models/`**: provider and model types (`providers.py`) and Smart Field types (`smart_fields.py`).
- **`src/app_state.py`** (`AppStateManager`): account and subscription state, and the pure access checks built on it. **`src/generation_access.py`** opens the web app when generation is blocked.
- **`src/config.py`**: the add-on config (`config.json`). **`src/constants.py`**: limits and other static values.

## Web UI and the local server

- **`web/`** is the React app (Vite, TypeScript, Tailwind, Zustand). `scripts/build.sh` builds it into `src/web/static/`.
- **`src/local_server.py`** serves it at `http://127.0.0.1:24766/app`. **`src/web_app.py`** and **`src/ui/web_app_dialog.py`** show it in a Qt webview.
- Anki owns all state, and the UI is a projection of it. The UI reads state from a single SSE stream (`GET /api/events`) and sends changes as commands (`POST /api/command`). **`src/event_bus.py`** and **`src/web/`** (hook adapters and DTOs) feed that stream.
- In `web/src/`, `features/` has one folder per screen. `store/appStore.ts` holds the state from the stream, `services/sse.ts` and `services/commands.ts` talk to the local server, `lib/i18n/` holds the translations, and `dev/` holds the mock state that `?mock=1` loads.
- In development, Vite serves the app on `http://localhost:5173/app/` with hot reload, and dev builds of the add-on point the webview there.

## Remaining Qt UI

**`src/ui/`** holds the Qt UI that's left: the editor's right-click menu and custom prompts (`field_menu.py`, `custom_prompt.py` and its option widgets), the sparkle effect, the rate dialog and the changelog.

## Utilities

**`src/utils/notes_utils.py`** has note type and field helpers, **`src/decks.py`** deck helpers, and **`src/media_utils.py`** media file naming.
