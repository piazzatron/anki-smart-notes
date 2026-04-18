# v2.18.0

- Sign in and sign up now open in your default browser, with passkey and password manager support.
- Add one-click request feature / report bug UI.

# v2.17.0

- Add VoiceVox: Free, best in class Japanese TTS with 29 character voices and 87 voice styles.

# v2.16.0

- Add Gemini models: Gemini 3.1 Pro, Gemini 3 Flash, and Gemini 3.1 Flash Lite.
- Add OpenAI TTS model gpt-4o-mini-tts. Higher quality than existing TTS-1 model.
- UX improvement: Batches are now cancellable.
- UX improvement: Allow editing existing Smart Fields target field, note type, and deck.

# v2.15.0

- Add new image models: GPT Image 1.5, Nano Banana 2, and Z-Image Turbo. Deprecate Flux Schnell.
- Upgrade Anthropic models to Claude Opus 4.6, Sonnet 4.6, and Haiku 4.5.
- Add optional web search for chat fields. When enabled, OpenAI and Anthropic models can search the web for current information. Images found in search results are automatically downloaded and saved to Anki.

# v2.14.0

- Unify credits: text, TTS, and image generation now all draw from the same credits pool. This should result in increased credit limits across all plans, potentially substantially, depending on your use case.

# v2.13.0

- Add new ElevenLabs V3 model and more affordable Flash V2.5 model (replacing Turbo 2.5).
- Add additional ElevenLabs Vietnamese voices.

# v2.12.0

- NEW TTS voices: 600 new Azure voices, 74 new Google Chirp voices.
- Improve voice selection UX.
- Bug fixes.

# v2.11.0

- Upgrade Anthropic to Sonnet 4.0, Opus 4.1, and Haiku 3.5 models.
- Bug fix: fix bug in cycle detection for complex prompts.
- Additional bug fixes.

# v2.10.0

- Add support for GPT-5 models, deprecate all 4 series models except 4o-mini.
- Bug fix: right clicking on fields during add card flow now opens context menu properly.

# v2.9.0

- Add support for new OpenAI models: 4.1, 4.1-mini, 4.1-nano, o4-mini, o3. If you're currently on 4o, try 4.1: it's cheaper and better!
- Improve UI for explaining cost differences between models.
- Migrate users on deprecated o1-mini model to o4-mini.

# v2.8.0

- Bug fix: notes that have multiple associated cards were processed repeatedly during batch generation. If you were affected by this, please email support@smart-notes.xyz!
- Feature: Right click on a prompt in the table view to copy it (from @danielpmichalski)

# v2.7.0

- Added OpenAI o1-mini reasoning model.
- No longer block UI with progress bar when generating individual cards.
- Fixed bug with ElevenLabs voices that made premium + ultra premium use the same voice.

# v2.6.0

- Adds support for DeepSeek-v3, a new language model that has high performance and cheap pricing. Try it out!

# v2.5.0

- New feature: Image generation Smart Fields!
- New feature: custom text/TTS/image generation via right clicking a field in the editor.

# v2.4.0

- Bug fix: you can now generate notes while the preview window is open, and the preview will automatically update.
- Bug fix: fixed overflowing add prompts UI for note types with many fields.

# v2.3.0

- Adds two new configurable pre-processing features:
- 1. Text prompts will convert markdown into HTML to properly render bold/italics/newlines/etc (enabled by default)
- 2. TTS will now strip out HTML by before creating speech (enabled by default)

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
