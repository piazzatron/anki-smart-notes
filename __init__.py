from typing import List, Callable
from aqt import gui_hooks, editor, mw
from aqt.operations import QueryOp
from anki.cards import Card
import requests

# TODO: sort imports...

# packages_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), "env/lib/python3.11/site-packages")
# print(packages_dir)
# sys.path.append(packages_dir)




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

def make_prompt(expression: str):
    return f"You are to provide an example sentence in Japanese for the word {expression}. Use only simple (N5) vocab and grammar.  Respond only with the Japanese example sentence followed by the english translation in paranthesis, nothing else."

def on_editor(buttons: List[str], e: editor.Editor):
    def fn(editor: editor.Editor):
        note = editor.note
        if not note:
            print("Error: no note found")
            return

        expression = note["Expression"]
        prompt = make_prompt(expression)

        def on_success(msg: str):
            note["Example"] = msg
            editor.loadNote()
            print("RAN THE THING IN BAC KGROUND")

        get_chat_response_in_background(prompt, on_success)

    button = e.addButton(cmd="Fill out stuff", func=fn, icon="!")
    buttons.append(button)

def on_review(card: Card):
    print("Reviewing...")
    note = card.note()
    example = note["Example"]
    if not example:
        prompt =  make_prompt(note["Expression"])

        def on_success(msg: str):
            note["Example"] = msg
            note["ExampleTTS"] = ""

            if not mw:
                print("Error: mw not found")
                return

            mw.col.update_note(note)
            card.load()
            print("Updated example sentence")

        get_chat_response_in_background(prompt, on_success)
    else:
        print("Example sentence already exists")


gui_hooks.editor_did_init_buttons.append(on_editor)
gui_hooks.reviewer_did_show_question.append(on_review)