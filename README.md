# **Smart Notes** - supercharge Anki with AI generated fields ✨

Use AI / ChatGPT to automatically & flexibly generate fields with {{templated}} prompting.

## Usage

1.  **Tools > Smart Notes:** set your <a href="https://platform.openai.com/api-keys">OpenAI API Key.</a>
2.  **Add Smart Fields** (AI generated fields).

    Set a note type, target card, and prompt.

    Prompts can reference any other field on the card with {{double curly braces}}.

    ![Create Field](https://github.com/piazzatron/anki-smart-notes/blob/readme/resources/screenshots/create_field.gif?raw=true)

3.  **Sit back** 😎

    Generate fields automatically during review, in edit/add, or batched in the card browser.

    ![Generate Field](https://github.com/piazzatron/anki-smart-notes/blob/readme/resources/screenshots/generate_prompt.gif?raw=true)

## Features

**Multiple ways to generate cards:**

1. **Automatically at review:** A sparkle emoji will briefly shimmer. (We love sparkle).
   This mode is particularly nice if you import notes via AnkiConnect (Yomichan, etc.) - no effort required.

   <img src="https://github.com/piazzatron/anki-smart-notes/blob/readme/resources/screenshots/sparkle.gif?raw=true" />

2. **Add/Edit:** (Re)Generate entire card with the ✨ button.

   <img src="https://github.com/piazzatron/anki-smart-notes/blob/readme/resources/screenshots/editor_button.png?raw=true" height="200px" />

3. **Individual Fields:** Right click on a field to (re)generate individual fields.

   <img src="https://github.com/piazzatron/anki-smart-notes/blob/readme/resources/screenshots/per_field.png?raw=true" height="300px" />

4. **Batch process:** Browser shift + right click to process multiple notes with lightning fast batch processing (it's seriously fast). _Whole deck processing soon :)_

   <img src="https://github.com/piazzatron/anki-smart-notes/blob/readme/resources/screenshots/batch.png?raw=true" height="250px" />

**Use any OpenAI model**

Tools > Smart Notes > Advanced. Select from the newest gpt-4o to cheapest 3.5-turbo

**Create complex prompts**

Smart fields can reference as many other fields on your card as you like. Smart fields can't reference other smart fields – yet.

_Smart Notes was initially inspired by <a href="https://ankiweb.net/shared/info/1416178071">Intellifiller</a>, which is sadly no longer supported in current Anki versions._

## Use Cases

- Generate example sentence for language study
- Generate memorable mmemonics
- Break down & summarize complicated sentences
- ... so many more!

## Additional Info

**Installation**
Restart Anki once you've installed the add-on. You will need an <a href="https://platform.openai.com/api-keys">OpenAI API key.</a>

**Cost** (to OpenAI, not to me 😢)

Free users can use gpt-3.5-turbo but are <a href="https://platform.openai.com/docs/guides/rate-limits/usage-tiers">limited to 3 requests/min.</a>

For paid users, <a href="https://openai.com/api/pricing/">prices are per token</a> - expect to pay a few tenths of a penny per call, but YMMV.

## Help and Support

Found a bug or want to request a feature? File an <a href="https://github.com/piazzatron/anki-smart-notes/issues"> issue on Github </a>.

Enjoying this addon? Please rate it 👍.
