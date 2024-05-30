from typing import List, Callable
import re
from aqt import gui_hooks, editor, mw
from aqt.operations import QueryOp
from anki.cards import Card
from anki.notes import Note
import requests

# TODO: sort imports...

# packages_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), "env/lib/python3.11/site-packages")
# print(packages_dir)
# sys.path.append(packages_dir)


config = mw.addonManager.getConfig(__name__)
OPEN_AI_KEY = config.get("openai_api_key")

# Create an OpenAPI Client
class OpenAIClient:
    def __init__(self, api_key):
        self.api_key = api_key

    def get_chat_response(self, prompt: str):
        r = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {self.api_key}",
            },
            json={"model": "gpt-4", "messages": [{"role": "user", "content": prompt}]},
        )

        resp = r.json()
        msg = resp["choices"][0]["message"]["content"]
        return msg

def get_chat_response_in_background(prompt: str, on_success: Callable):
    if not mw:
        print("Error: mw not found")
        return

    op = QueryOp(
        parent=mw,
        op=lambda _: client.get_chat_response(prompt),
        success=on_success,
    )

    op.run_in_background()


client = OpenAIClient(OPEN_AI_KEY)

def get_prompt_fields_lower(prompt: str):
    pattern = r"\{\{(.+?)\}\}"
    fields = re.findall(pattern, prompt)
    return [field.lower() for field in fields]

def validate_prompt(prompt: str, note: None):
    prompt_fields = get_prompt_fields_lower(prompt)

    all_note_fields = {field.lower(): value for field, value in note.items()}

    for prompt_field in prompt_fields:
        if prompt_field not in all_note_fields:
            return False

    return True


def generate_prompt(prompt: str, note: Note):
    # Bunch of extra logic to make this whole process case insensitive

    # Regex to pull out any words enclosed in double curly braces
    fields = get_prompt_fields_lower(prompt)
    pattern = r"\{\{(.+?)\}\}"

    # field.lower() -> value map
    all_note_fields = {field.lower(): value for field, value in note.items()}

    # Lowercase the characters inside {{}} in the prompt
    prompt = re.sub(pattern, lambda x: "{{" + x.group(1).lower() + "}}", prompt)

    for field in fields:
        value = all_note_fields.get(field, "")
        prompt = prompt.replace("{{" + field + "}}", value)

    print("Processed prompt: ", prompt)
    return prompt

def async_process_note(note: Note, on_success: Callable, overwrite_fields=False):
    prompt = generate_prompt(make_prompt(), note)

    def wrapped_on_success(msg: str):
        note["Example"] = msg
        # Perform UI side effects
        on_success()
        print("Successfully ran in background")

    get_chat_response_in_background(prompt, wrapped_on_success)

# TODO: deleteme
def make_prompt():
    return "You are to provide an example sentence in Japanese for the word {{expression}}. Use only simple (N5) vocab and grammar.  Respond only with the Japanese example sentence followed by the english translation in paranthesis, nothing else."

def on_editor(buttons: List[str], e: editor.Editor):
    def fn(editor: editor.Editor):
        note = editor.note
        if not note:
            print("Error: no note found")
            return

        async_process_note(note=note, on_success=lambda: editor.loadNote())

    button = e.addButton(cmd="Fill out stuff", func=fn, icon="!")
    buttons.append(button)

def on_review(card: Card):
    print("Reviewing...")
    note = card.note()
    # TODO: need to handle field value already existing
    example = note["Example"]

    if not example:
        def update_note():
            if not mw:
                print("Error: mw not found")
                return

            mw.col.update_note(note)
            card.load()
            print("Updated on review")

        async_process_note(note=note, on_success=update_note)
    else:
        print("Example sentence already exists")


gui_hooks.editor_did_init_buttons.append(on_editor)

# TODO: I think this should be 'card did show'?
gui_hooks.reviewer_did_show_question.append(on_review)