# Smart Notes ✨

Smart Notes is the Anki AI toolkit that adds AI text, audio, and images to thousands of cards in minutes. Define Smart Fields for your note types, reference existing fields in prompts, and let Smart Notes generate text, text-to-speech audio, and images during review, in the editor, or in bulk from the browser.

## 📚 Documentation & Installation

Find full documentation and setup instructions on the [Smart Notes website](https://smart-notes.xyz) and [AnkiWeb](https://ankiweb.net/shared/info/1531888719). Install with add-on code `1531888719`.

<img src="https://smart-notes.xyz/example_field.gif" alt="Smart Notes generating an AI field in Anki" height="350" />

## 🏗️ Repository Architecture

This repository contains the GPL-licensed Anki add-on. The add-on integrates with Anki's Qt UI, stores local Smart Field configuration, and talks to the Smart Notes backend for model generation, subscription state, and usage tracking.

The production backend and marketing site live outside this public plugin repository. The backend is private and is not distributed under the GPL; the plugin code in this repository is distributed under GPL v3. See [LICENSE](LICENSE).

## 💬 Support

Found a bug or want to request a feature? Open a [GitHub issue](https://github.com/piazzatron/anki-smart-notes/issues), email [support@smart-notes.xyz](mailto:support@smart-notes.xyz), or join the [Discord](https://discord.gg/kxGaWpkTGr).

Enjoying Smart Notes? [Please rate it on AnkiWeb](https://ankiweb.net/shared/info/1531888719) to help other Anki users find it.

## 🤝 Contributing

PRs are welcome. [ARCHITECTURE.md](ARCHITECTURE.md) explains how the code fits together.

Set up a virtualenv in `.venv` and install `requirements.txt` into it. The web UI in `web/` needs [Bun](https://bun.sh).

| Command | What it does |
|---|---|
| `./scripts/build.sh check` | Format check, lint and typecheck. Run it before opening a PR |
| `./scripts/build.sh fix` | Fix formatting and lint issues |
| `./scripts/build.sh typecheck` | Typecheck only |
| `source .venv/bin/activate && python -m pytest` | Python tests |
| `./scripts/build.sh build` | Build the add-on package, with the web UI bundled |
| `bun run dev` (in `web/`) | Web UI dev server on `:5173`. Dev builds of the add-on load it from there |
| `bun run check` / `bun run test` (in `web/`) | Web UI checks and tests |

Packaged builds include only the dependencies `scripts/build.sh` copies into `dist/vendor`. When you add or remove a runtime dependency in `requirements.txt`, update that list too. Vendored packages run on Anki's own Python, so pin them to versions that still support Python 3.9 (Anki 2.1.50 to 25.02); `uv pip compile --python-version 3.9` resolves such a set.

### Supported Anki versions

Smart Notes supports Anki 2.1.20 and later, the range set on the AnkiWeb listing. `requirements.txt` pins Anki 24.4.1 for development. CI also runs the checks and tests against the newest Anki, the version in `.github/workflows/ci.yml`'s matrix. To reproduce that locally, install the requirements into a scratch venv, then run `pip install "anki==X" "aqt==X" "protobuf>=6,<8"`. Run pyright from a copy of the folder without `.venv`, since `pyrightconfig.json` otherwise reads `.venv`.

## 🎨 Credits

The web UI's artwork is not covered by the GPL:

- Icons: [Solar](https://www.figma.com/community/file/1166831539721848736) by 480 Design, licensed under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/).
- Page-title emoji: [Noto Emoji](https://github.com/googlefonts/noto-emoji) by Google, licensed under Apache 2.0.

## 📝 Changelog

See [changelog.md](changelog.md) for recent changes.
