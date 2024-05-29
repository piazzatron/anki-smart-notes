from typing import List
from aqt import gui_hooks, editor
import requests

# TODO: sort imports...

# packages_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), "env/lib/python3.11/site-packages")
# print(packages_dir)
# sys.path.append(packages_dir)




def on_editor(buttons: List[str], e: editor.Editor):
    def fn(editor: editor.Editor):
        note = editor.note
        expression = note["Expression"]

        r = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {OPEN_AI_KEY}",
            },
            json={
              "model": "gpt-4",
              "messages": [
                {
                    "role": "user",
                    "content": f"You are to provide an example sentence in Japanese for the word {expression}. Use only simple (N5) vocab and grammar.  Respond only with the Japanese example sentence followed by the english translation in paranthesis, nothing else.",
                }
              ]
            }
        )

        resp = r.json()
        msg = resp["choices"][0]["message"]["content"]
        print(msg)
        note["Example"] = msg
        editor.loadNote()



    button = e.addButton(cmd="Fill out stuff", func=fn, icon="!")
    buttons.append(button)



gui_hooks.editor_did_init_buttons.append(on_editor)
