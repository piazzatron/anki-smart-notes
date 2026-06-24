# Smart Notes

[![CI](https://github.com/piazzatron/anki-smart-notes/actions/workflows/ci.yml/badge.svg)](https://github.com/piazzatron/anki-smart-notes/actions/workflows/ci.yml)

Smart Notes is the Anki AI toolkit that adds AI text, audio, and images to thousands of cards in minutes. Define Smart Fields for your note types, reference existing fields in prompts, and let Smart Notes generate text, text-to-speech audio, and images during review, in the editor, or in bulk from the browser.

Learn more at [smart-notes.xyz](https://smart-notes.xyz). Install from AnkiWeb with add-on code `1531888719`.

<img src="https://smart-notes.xyz/example_field.gif" alt="Smart Notes generating an AI field in Anki" height="350" />

## Repository Architecture

This repository contains the GPL-licensed Anki add-on. The add-on integrates with Anki's Qt UI, stores local Smart Field configuration, and talks to the Smart Notes backend for model generation, subscription state, and usage tracking.

The production backend and marketing site live outside this public plugin repository. The backend is private and is not distributed under the GPL; the plugin code in this repository is distributed under GPL v3. See [LICENSE](LICENSE).

## Support

Found a bug or want to request a feature? Open a [GitHub issue](https://github.com/piazzatron/anki-smart-notes/issues), email [support@smart-notes.xyz](mailto:support@smart-notes.xyz), or join the [Discord](https://discord.gg/kxGaWpkTGr).

Enjoying Smart Notes? [Please rate it on AnkiWeb](https://ankiweb.net/shared/info/1531888719) to help other Anki users find it.

## Contributing

PRs are welcome. This repo uses Python with typechecking, linting, formatting, and tests; run `./scripts/build.sh check` before opening a PR.

## Changelog

See [changelog.md](changelog.md) for recent changes.

_Smart Notes owes a debt of gratitude for inspiration to [Intellifiller](https://ankiweb.net/shared/info/1416178071)._
