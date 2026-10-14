# About

- This repo is an extension for the Anki app called Anki Smart Notes. 
- Anki Smart Notes adds functionality to Anki to allow fields to be AI generated. This works for both text, audio, and images.


# Code Style and Practices
- Use modern Python. Make sure your code is fully typed.
- Always put imports at the top of files, never inside functions or methods
- Prefix private top level helper defs with `_`. Keep public APIs, Anki hook callbacks, Qt signal callbacks, and other framework entry points unprefixed.
- Avoid unnecessary abstractions. Don't extract helper functions or add parameters unless the operation is actually reused. Prefer inlining logic with a brief comment over creating a single-use helper. Extra parameters that just proxy a check (e.g. passing `self.mode == "edit"` as a bool arg) add indirection — just check the condition directly in the method body.

## Logging Levels
- Prefer `info` for lifecycle and support-diagnostic events that help debug real user sessions: startup, shutdown, migrations, retries, auth flow milestones, feature flag refreshes, profile/config transitions, and external-service request outcomes.
- Use `debug` for sensitive data, verbose payloads, prompt/model contents, provider response bodies, API request arguments, stack traces, UI state churn, per-keystroke updates, per-field processing details, and any log that can fire extremely frequently during normal interaction.
- When promoting a log from `debug` to `info`, check whether the message exposes user content, tokens, identifiers, or noisy internals. Prefer redacted summaries at `info` and keep full details at `debug` only when useful.

# Important Commands
- Use `./scripts/build.sh check` to run all code quality checks (format, lint, typecheck)
- Use `./scripts/build.sh typecheck` to run only type checking
- Use `./scripts/build.sh fix` to automatically fix formatting and linting issues
- Use `source .venv/bin/activate && python -m pytest` to run tests.
- When adding or removing runtime dependencies in `requirements.txt`, also update the vendored dependency list in `scripts/build.sh`; packaged Anki builds only include dependencies copied into `dist/vendor`.

## Supported Anki Versions

- Smart Notes supports Anki 2.1.20+ (the range set on the AnkiWeb listing). The maintainer runs Anki 26.09.3.
- Anki's Python API changes between releases (25.09 replaced `SearchNode.Field.is_re` with `mode`; hooks like `addon_manager_will_install_addon` only exist from 2.1.65). Code that touches Anki APIs must work across the whole supported range: prefer APIs that exist in every version, and guard the ones that don't.
- `requirements.txt` pins Anki 24.4.1. CI also runs checks and tests on the newest Anki (the version in `.github/workflows/ci.yml`'s matrix); bump it when Anki releases. To reproduce that leg locally, install requirements into a scratch venv, then `pip install "anki==X" "aqt==X" "protobuf>=6,<8"`. Run pyright from a copy without `.venv`, since `pyrightconfig.json` otherwise reads the repo's `.venv`.

## Changelog Versioning

- `manifest.json`'s `human_version` is the currently shipped version.
- Add changelog entries only for significant new user-facing features. Do not add entries for small UI polish, refactors, maintenance, or similar incremental work unless the user explicitly requests it.
- Before editing `changelog.md`, show the user the exact proposed version heading and bullets and wait for explicit confirmation.
- If the latest `changelog.md` entry is ahead of `human_version`, that version hasn't shipped yet: add to that entry instead of creating a new one.
- Only start a new changelog version entry once the prior one has been released (`human_version` matches or exceeds it).

## Web UI Visual Testing

- For Smart Notes web UI layout and interaction verification, follow the shared `anki-ui-testing` skill at `../skills/anki-ui-testing/SKILL.md`.

## Web UI Translations

- While iterating, edit only `web/src/lib/i18n/locales/en.json`. Run `bun run translate` (in `web/`) once, right before pushing, since strings usually change several times first.
- `translate` runs `claude -p` on your Claude Code login (no API key), 8 locales at a time, and takes about a minute. A string whose reply breaks a `{{placeholder}}` or markup tag is retried with a stronger model. Strings that still fail are left out of their locale, listed at the end, and the run exits non-zero; run it again to retry just those.
- `bun run check` (and CI) fails until then: `scripts/checkTranslations.ts` rejects missing or removed keys, broken placeholders, and English that is new or reworded since the last full translate run (tracked in `scripts/translationSources.json`). `translate` re-translates exactly those strings and updates that file. Expect only this check to fail mid-iteration.

# Code Structure
- This is a Python3 codebase which takes full advantage of strong typing for static analysis.
- UI specific code lives in `src/ui`
- The code entry point is `main.py` → `hooks.py`, which sets up the Anki UI and initializes key classes.

## Key Architecture Components

The specs in the top-level repo's `/specs` (start with `note-generation.md` and `web-ui-architecture.md`) describe how these fit together.

### Entry Point & Flow
- **`main.py`**: Entry point that creates `NoteProcessor` and calls `setup_hooks()`.
- **`hooks.py`**: Anki hooks, menus, editor button, and the startup/profile lifecycle (migrations, local server, background evaluators).

### Generation
- **`note_proccessor.py`** (`NoteProcessor`): Generates a note's Smart Fields in dependency order; batch, single-card, and single-field entry points.
- **`dag.py`** / **`nodes.py`**: The dependency graph between Smart Fields that reference other fields. Cycles are rejected when a Smart Field is saved (`SmartFieldService`); `NoteProcessor` stops rather than spinning if one reaches the database anyway.
- **`field_resolver.py`**: Generates one field by type (chat, TTS, image) and writes media.
- **`prompt_fields.py`** / **`prompt_helpers.py`**: `{{field}}` extraction and interpolation.
- **`review_time_evaluator.py`** / **`add_time_evaluator.py`**: Background generation during review and after notes are added.
- **`chat_provider.py`**, **`tts_provider.py`**, **`image_provider.py`** → **`api_client.py`**: Calls to the Smart Notes server. **`open_ai_client.py`** is the legacy bring-your-own-key path.

### State, Persistence & Configuration
- **`services/`**: `smart_field_service.py` (Smart Fields and generation defaults in SQLite), `settings_service.py`, `prompt_test_service.py`, `auth_service.py`.
- **`database/`**: SQLite connection and migrations (`migrations.py` header explains the order).
- **`models/`**: Provider/model types (`providers.py`) and Smart Field types (`smart_fields.py`).
- **`app_state.py`** (`AppStateManager`): Account/subscription state and pure access checks; **`generation_access.py`** opens the web app when generation is blocked.
- **`config.py`**: Add-on config (`config.json`); **`constants.py`**: limits and static values.

### Web UI and Local Server
- **`web/`** (React app) is served by **`local_server.py`** and shown by **`web_app.py`** / **`ui/web_app_dialog.py`**. **`event_bus.py`** and **`src/web/`** (hook adapters, DTOs) feed it state.
- **`src/ui/`**: The remaining Qt UI — the editor's right-click menu and custom prompts (`field_menu.py`, `custom_prompt.py` and its option widgets), the sparkle effect, the rate dialog, and the changelog.

### Utilities
- **`utils/notes_utils.py`**: Note type and field helpers; **`decks.py`**: deck helpers; **`media_utils.py`**: media file naming.

# Creating New Files
- All new files must have the following license information at the very top.

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
