# **Smart Notes** - Anki + AI generated fields ✨

</br>

## Use AI / ChatGPT to automatically generate any field in your notes.

For example, ChatGPT is very powerful for language learners, who might use it to generate example sentences for new vocab. This plugin brings that whole process into Anki: set it up once, and every new piece of vocab will automatically receive an AI generated example sentence.

**Write a prompt, associate it with a note type and field, and Smart Notes will automatically generate that field for you at review time – or generate groups of notes with a single click.**

<img src="https://piazzatron.github.io/anki-smart-notes/resources/screenshots/create_field.gif" />
</br>
</br>

<img src="https://piazzatron.github.io/anki-smart-notes/resources/screenshots/generate_prompt.gif" />

</br>

Language learning, summarization, you name it – automate the busywork of card creation so you have more time for studying!

</br>

# Usage

</br>

## 1. **Installation**:

Tools > Addons > Get Addon, paste in plugin id `1531888719`. Restart Anki.

## 2. **Set your OpenAI API Key:**

This plugin requires an OpenAI API key: <a href="https://platform.openai.com/api-keys">get one here.</a>

Tools > Smart Notes > API key.

## 3. **Add Smart Fields** (AI generated fields):

</br>

**Smart fields are AI generated fields associated with a particular card type.**
They may reference other fields, and you can have as many smart fields as you like.

</br>

1. Click Tools > Smart Notes > Add

2. Pick the `card type` and `target field` you want to automatically generate.

3. Then, write the `prompt` that will be automatically sent to OpenAI/ChatGPT to generate the `target field`.

</br>

### Writing a Prompt

A prompt may reference any other field on the card via `{{double curly braces}}`.

For example, if you're studying a language and want to generate a mmemonic to aid in memorization, you might make a prompt like this (assuming you have a field called "vocab"):

```
Create a simple, memorable mmemonic in Japanese for the word {{vocab}}. Reply with only the mmemonic.
```

It's often useful to tell language model to "only reply" with the phrase you care about.

_You can't reference the target field, or other smart fields – but the addon will validate your prompt, so don't worry!_

</br>

## 4. **Automatically generate notes** 😎

Generate smart notes during review, in edit or add flows, or batched in the card browser.

</br>

</br>

### **Generate during review**

Smart fields are automatically generated in the background at review time.

This is approach is super useful if you import notes via AnkiConnect (Yomichan, etc) - simply set up your smart fields and no further effort required.

 <img src="https://piazzatron.github.io/anki-smart-notes/resources/screenshots/sparkle.gif?raw=true" />

_A sparkle emoji will briefly show (we love sparkle)._

Note that you can turn automatic generation off in _Smart Notes > Advanced_.

</br>
</br>

### **Generate when adding or editing cards**

Smart fields can also be generated prior to review. To (re)generate all smart fields on a note, simply click the ✨ button in the editor:

<img src="https://piazzatron.github.io/anki-smart-notes/resources/screenshots/editor_button.png?raw=true" height="200px" />

</br>
</br>

Alternatively, to generate a single smart field and leave the rest of the note untouched, right click an individual field in the editor and click "Generate Smart Field":

<img src="https://piazzatron.github.io/anki-smart-notes/resources/screenshots/per_field.png?raw=true" height="300px" />

</br>
</br>

### **Generating Multiple Notes**

<img src="https://piazzatron.github.io/anki-smart-notes/resources/screenshots/batch.png?raw=true" height="250px" />

In the notes browser, select as many cards as you'd like and then **right click > generate smart fields** to generate multiple notes with speedy batch processing (it's v fast)!

**Note: You'll need a paid OpenAI key to batch edit – unpaid keys are limited to 3 requests/min.**

_Whole deck processing soon :)_

</br>

# Additional Features

### **Use any OpenAI model**

**Tools > Smart Notes > Advanced:** Select from the newest `gpt-4o` to cheapest `gpt-3.5-turbo` (default).

_At this time, free API tier users only have access to `gpt-3.5-turbo`._

</br>

### **Create complex prompts**

Smart fields can reference as many other fields on your card as you like.

</br>

# Additional Info

_Smart Notes owes a debt of gratitude for inspiration to <a href="https://ankiweb.net/shared/info/1416178071">Intellifiller.</a>_

**Cost** (to OpenAI, not to me 😢)

- Free users can use gpt-3.5-turbo but are <a href="https://platform.openai.com/docs/guides/rate-limits/usage-tiers">limited to 3 requests/min.</a>
- For paid users, <a href="https://openai.com/api/pricing/">prices are per token</a> - expect to pay a few tenths of a penny per call, but YMMV.

</br>

## Help and Support

Found a bug or want to request a feature? File an <a href="https://github.com/piazzatron/anki-smart-notes/issues"> issue on Github </a>.

Enjoying this addon? <a href="https://ankiweb.net/shared/info/1531888719">Please rate it to help others find it.👍</a>
