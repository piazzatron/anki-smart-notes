# **Smart Notes** - supercharge Anki with AI generated fields ✨

</br>

## Use AI / ChatGPT to automatically & flexibly generate fields with `{{templated}}` prompts.

</br>

# Usage

1.  **Tools > Smart Notes:** set your <a href="https://platform.openai.com/api-keys">OpenAI API Key.</a>
2.  **Add Smart Fields** (AI generated fields):

- Set a note type, target field, and prompt.
- Prompts can reference any other field on the card with `{{double curly braces}}.`

  <img src="https://piazzatron.github.io/anki-smart-notes/resources/screenshots/create_field.gif" />

3.  **Generate your cards** 😎

    Generate fields automatically during review, in edit/add, or batched in the card browser.

    <img src="https://piazzatron.github.io/anki-smart-notes/resources/screenshots/generate_prompt.gif" />

</br>

# Features

</br>

### **Multiple ways to generate cards:**

1. **Automatically at review:**
   Seamlessly generate fields in the background at review time.

   Nice if you import notes via AnkiConnect (Yomichan, etc.) - no effort required.

   A sparkle emoji will briefly show (we love sparkle).

 <img src="https://piazzatron.github.io/anki-smart-notes/resources/screenshots/sparkle.gif?raw=true" />
</br>
</br>

2. **Add/Edit:** (Re)Generate entire card with the ✨ button.

   <img src="https://piazzatron.github.io/anki-smart-notes/resources/screenshots/editor_button.png?raw=true" height="200px" />

</br>

3. **Individual Fields:** Right click on a field to (re)generate individual fields.

   <img src="https://piazzatron.github.io/anki-smart-notes/resources/screenshots/per_field.png?raw=true" height="300px" />

</br>

4. **Batch process:** Browser shift + right click to process multiple notes with lightning fast batch processing (it's seriously fast). _Whole deck processing soon :)_

   <img src="https://piazzatron.github.io/anki-smart-notes/resources/screenshots/batch.png?raw=true" height="250px" />

</br>

### **Use any OpenAI model**

Tools > Smart Notes > Advanced. Select from the newest `gpt-4o` to cheapest `gpt-3.5-turbo` (default).

_At this time, free API tier users only have access to `gpt-3.5-turbo`._

</br>

### **Create complex prompts**

Smart fields can reference as many other fields on your card as you like. Smart fields can't reference other smart fields – yet.

</br>

# Use Cases

- Generate example sentence for language study
- Generate memorable mmemonics
- Break down & summarize complicated sentences
- ... so many more!

</br>

# Additional Info

_Smart Notes owes a debt of gratitude for inspiration to <a href="https://ankiweb.net/shared/info/1416178071">Intellifiller.</a>_

**Installation**

Restart Anki once you've installed the add-on.

**Cost** (to OpenAI, not to me 😢)

- Free users can use gpt-3.5-turbo but are <a href="https://platform.openai.com/docs/guides/rate-limits/usage-tiers">limited to 3 requests/min.</a>
- For paid users, <a href="https://openai.com/api/pricing/">prices are per token</a> - expect to pay a few tenths of a penny per call, but YMMV.

**Prompts**

OpenAI has some <a href="https://help.openai.com/en/articles/6654000-best-practices-for-prompt-engineering-with-the-openai-api">nice guides to writing effective prompts.</a>

</br>

## Help and Support

Found a bug or want to request a feature? File an <a href="https://github.com/piazzatron/anki-smart-notes/issues"> issue on Github </a>.

Enjoying this addon? Please rate it 👍.
