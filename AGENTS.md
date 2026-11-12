Read @README.md and @ARCHITECTURE.md before working here: they cover what the add-on is, how to build, check and test it, the supported Anki versions and how the code fits together. The top-level `specs/` describe behavior in depth (start with `note-generation.md` and `web-ui-architecture.md`). In the monorepo, run checks and tests with `cli/sn check plugin` and `cli/sn test plugin`.

# Logging Levels
- Prefer `info` for lifecycle and support-diagnostic events that help debug real user sessions: startup, shutdown, migrations, retries, auth flow milestones, feature flag refreshes, profile/config transitions, and external-service request outcomes.
- Use `debug` for sensitive data, verbose payloads, prompt/model contents, provider response bodies, API request arguments, stack traces, UI state churn, per-keystroke updates, per-field processing details, and any log that can fire extremely frequently during normal interaction.
- When promoting a log from `debug` to `info`, check whether the message exposes user content, tokens, identifiers, or noisy internals. Prefer redacted summaries at `info` and keep full details at `debug` only when useful.

# Anki Version Compatibility

- Anki's Python API changes between releases (25.09 replaced `SearchNode.Field.is_re` with `mode`; hooks like `addon_manager_will_install_addon` only exist from 2.1.65). Code that touches Anki APIs must work across the whole supported range (see the README): prefer APIs that exist in every version, and guard the ones that don't.
- The maintainer runs Anki 26.09.3. When Anki releases, bump the newest-Anki version in the monorepo's `.github/workflows/plugin-ci.yml` matrix.

# Creating New Files
- Every new file starts with the GPL license header: copy lines 1–18 of [`__init__.py`](__init__.py).
