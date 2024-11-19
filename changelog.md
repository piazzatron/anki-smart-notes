# v2.5.0

- Image generation!
- Right click on an editor to field to generate custom text/TTS/images

# v2.4.0

- Bug fix: you can now generate notes while the preview window is open, and the preview will automatically update.
- Bug fix: fixed overflowing add prompts UI for note types with many fields.

# v2.3.0

- Adds two new configurable pre-processing features:
- 1) Text prompts will convert markdown into HTML to properly render bold/italics/newlines/etc (enabled by default)
- 2) TTS will now strip out HTML by before creating speech (enabled by default)


# v2.2.0

- New feature: associate a Smart Field with a deck to easily reuse the same note type across different decks!
- Increase default OpenAI temperature for more creative & random responses (if you previously set a custom temp, you'll have reset it).

# v2.1.0

- Fix bug affecting new text fields for some users 😓. Free Trials for all new users have been extended. 

# v2.0.0

- Add TTS support
- Add Claude support
- Add chained smart fields
- Add new subscription model

# v1.6.0

- Add support for new `gpt-4o-mini` model, removing the old `gpt-3.5-turbo`. Users on `gpt-3.5-turbo` are automatically migrated to `4o-mini`.
- Stability & UX improvements.

# v1.5.0

- Prompts may now reference empty fields. Control this behavior in settings > advanced.

# v1.4.0

- Manual fields: uncheck "Always Generate Smart Field" when creating a field to leave it empty by default. Editor > Right Click to generate it.
- Set a custom OpenAI endpoint via Settings > Advanced. Supports users who are unable to access the official OpenAI API.

# v1.3.0

- Improved regenerating smart field behavior:
- 1. For partially filled notes, the editor ✨ button will now only generate empty fields. Click ✨ a second time to regenerate the card from scratch.
- 2. Batch processing will now only generate empty fields by default. Configurable via Settings -> Advanced to regenerate the entire note.

# v1.2.0

- Support batch processing huge decks.
- Right click on a deck or note type in the browser to generate all notes.
- Fix bugs.

# v1.1.0

- Add hotkey: <b>Ctrl+Shift+G</b> (or <b>Cmd+Shift+G</b> on Mac) to generate fields in the editor.
- Clarify that this add-on requires a paid OpenAI API key (no free tier 🥺).
- Fix bugs.
