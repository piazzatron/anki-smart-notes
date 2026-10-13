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

## Changelog Versioning

- `manifest.json`'s `human_version` is the currently shipped version.
- Add changelog entries only for significant new user-facing features. Do not add entries for small UI polish, refactors, maintenance, or similar incremental work unless the user explicitly requests it.
- Before editing `changelog.md`, show the user the exact proposed version heading and bullets and wait for explicit confirmation.
- If the latest `changelog.md` entry is ahead of `human_version`, that version hasn't shipped yet: add to that entry instead of creating a new one.
- Only start a new changelog version entry once the prior one has been released (`human_version` matches or exceeds it).

## Web UI Visual Testing

- For Smart Notes web UI layout and interaction verification, follow the shared `anki-ui-testing` skill at `../skills/anki-ui-testing/SKILL.md`.

## Web UI Translations

- While iterating, edit only `web/src/lib/i18n/locales/en.json`. Run `bun run translate` (in `web/`) once, right before pushing. It is slow, and strings usually change several times first.
- `bun run check` (and CI) fails until then: `scripts/checkTranslations.ts` rejects missing or removed keys, broken placeholders, and English that is new or reworded since the last full translate run (tracked in `scripts/translationSources.json`). `translate` re-translates exactly those strings and updates that file. Expect only this check to fail mid-iteration.

# Code Structure
- This is a Python3 codebase which takes full advantage of strong typing for static analysis.
- UI specific code lives in `src/ui`
- The code entry point is `main.py` → `hooks.py`, which sets up the Anki UI and initializes key classes.

## Key Architecture Components

### Entry Point & Flow
- **`main.py`**: Entry point that creates `NoteProcessor` and calls `setup_hooks()` 
- **`hooks.py`**: Sets up all Anki UI hooks, menu items, buttons, and context menus. Initializes logging, config, and migrations. Contains the main UI integration logic.

### Core Processing Classes
- **`NoteProcessor`** (`note_proccessor.py`): Main orchestrator for processing notes/cards. Handles batch processing, single card processing, and manages the DAG execution flow.
- **`FieldProcessor`** (`field_processor.py`): Handles individual field processing based on type (chat, TTS, image). Routes to appropriate providers and handles response formatting.
- **`AppStateManager`** (`app_state.py`): Manages subscription state, capacity limits, and app unlock status. Handles transitions between subscription states.

### Field Processing System  
- **`dag.py`**: Creates Directed Acyclic Graph for field dependencies. Handles topological sorting and cycle detection for smart fields that reference other fields.
- **`nodes.py`**: `FieldNode` class representing individual fields in the DAG with dependencies, processing state, and metadata.
- **`prompts.py`**: Prompt interpolation, field extraction from prompts, and prompt management per note type/deck.

### Data Models & Configuration
- **`models.py`**: Type definitions for:
  - Chat/TTS/Image providers and models 
  - `SmartFieldType` ("chat", "tts", "image")
  - `FieldExtras` configuration per field
  - Provider/model mappings
- **`config.py`**: Global configuration management with persistence
- **`constants.py`**: Error messages, limits, and static values

### Provider Classes
- **`chat_provider.py`**: Handles OpenAI, Anthropic, DeepSeek chat completions
- **`tts_provider.py`**: Text-to-speech via OpenAI, ElevenLabs, Google
- **`image_provider.py`**: Image generation via Replicate (Flux models)
- **`open_ai_client.py`**: Legacy OpenAI client for users with API keys

### UI System (`src/ui/`)
- **Reactive Components**: Base classes for reactive UI widgets that update automatically
- **`addon_options_dialog.py`**: Main settings dialog
- **`field_menu.py`**: Context menu for individual fields 
- **`state_manager.py`**: Generic state management for UI components
- **Dialog Components**: Various specialized dialogs for prompts, subscriptions, etc.

### Utilities
- **`notes.py`**: Note type utilities, field validation, AI field detection
- **`decks.py`**: Deck-related utilities and caching
- **`utils.py`**: General utilities, async helpers, field extraction
- **`media_utils.py`**: Media file path generation for TTS/images 

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
