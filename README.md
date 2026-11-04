# Smart Notes ✨

<img src="https://smart-notes.xyz/github_header.gif" alt="Smart Notes filling in a Japanese card and a med-school card with AI text, audio and images" />

**Fill any field on your cards with AI text, audio and images.**

Smart Notes is an add-on for [Anki](https://apps.ankiweb.net), the spaced-repetition flashcard app. It turns any field on your note types into a Smart Field: describe what you want in plain language, like "a natural example sentence using this word", and Smart Notes fills it in with AI-generated text, text-to-speech audio or an image. Smart Fields can feed into each other, so one field's sentence can be read aloud or illustrated in the next.

Enhance your cards automatically in the background, generate individual fields by hand, or process your deck of 10,000 notes in a single click.

**Install:** in Anki, go to **Tools → Add-ons → Get Add-ons...** and enter `1531888719`. Smart Notes is paid, with a free trial: [see plans](https://smart-notes.xyz/prices). More on [AnkiWeb](https://ankiweb.net/shared/info/1531888719) and at [smart-notes.xyz](https://smart-notes.xyz).

- **Text models:** Auto, or GPT-6.1 Sol, GPT-6.1 Terra and GPT-6 Luna (OpenAI); Claude Opus 5.5, Sonnet 5.5 and Haiku 5.5 (Anthropic); Gemini 4 Argon, Gemini 3.8 Flash and Gemini 3.5 Flash-Lite (Google).
- **Image models:** GPT Image 2.5 (OpenAI), Nano Banana 2.1 and Nano Banana 2 Lite (Google) and Z-Image Turbo, plus image search.
- **Text-to-speech:** 1,000+ voices in 80+ languages from ElevenLabs, Google, Azure, OpenAI and VOICEVOX.
- **Works with** Anki 2.1.50 and later (Qt6 builds), including the latest Anki release, on Windows, macOS and Linux.

Smart Notes is actively maintained and kept up to date with the latest AI models and Anki releases: see [changelog.md](changelog.md) for every release.

## Support

Found a bug or want to request a feature? Open a [GitHub issue](https://github.com/piazzatron/anki-smart-notes/issues), email [support@smart-notes.xyz](mailto:support@smart-notes.xyz), or join the [Discord](https://discord.gg/kxGaWpkTGr).

Enjoying Smart Notes? [Please rate it on AnkiWeb](https://ankiweb.net/shared/info/1531888719) to help other Anki users find it.

## Contributing

This repository is the GPL-licensed Anki add-on, distributed under GPL v3 (see [LICENSE](LICENSE)). It integrates with Anki's Qt UI, stores Smart Field configuration locally, and talks to the Smart Notes backend for generation, subscription state and usage tracking. The backend and the marketing site are private and not distributed under the GPL.

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

Smart Notes supports Anki 2.1.50 and later, Qt6 builds only, since it imports `PyQt6` directly. Keep the AnkiWeb listing's version range to match. `requirements.txt` pins Anki 24.4.1 for development. CI also runs the checks and tests against the newest Anki release. To reproduce that locally, install the requirements into a scratch venv, then run `pip install "anki==X" "aqt==X" "protobuf>=6,<8"`. Run pyright from a copy of the folder without `.venv`, since `pyrightconfig.json` otherwise reads `.venv`.

## Credits

The web UI's artwork is not covered by the GPL:

- Icons: [Solar](https://www.figma.com/community/file/1166831539721848736) by 480 Design, licensed under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/).
- Page-title emoji: [Noto Emoji](https://github.com/googlefonts/noto-emoji) by Google, licensed under Apache 2.0.
