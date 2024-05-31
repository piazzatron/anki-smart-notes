from typing import List, Callable, TypedDict, Dict
import re
from aqt import gui_hooks, editor, mw
from aqt.operations import QueryOp
from anki.cards import Card
from anki.notes import Note
from aqt.qt import QAction, QDialog, QLabel, QGridLayout, QLineEdit, QDialogButtonBox
import requests

# TODO: sort imports...

# packages_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), "env/lib/python3.11/site-packages")
# print(packages_dir)
# sys.path.append(packages_dir)

class NoteTypeMap(TypedDict):
    fields: Dict[str, str]

class PromptMap(TypedDict):
    note_types: Dict[str, NoteTypeMap]

class Config:
    openai_api_key: str
    prompts_map: PromptMap
    openai_model: str # TODO: type this


    def __getattr__(self, key: str) -> object:
        if not mw:
            raise Exception("Error: mw not found")

        return mw.addonManager.getConfig(__name__).get(key)

    def __setattr__(self, name: str, value: object) -> None:
        if not mw:
            raise Exception("Error: mw not found")

        old_config = mw.addonManager.getConfig(__name__)
        if not old_config:
            raise Exception("Error: no config found")

        old_config[name] = value
        mw.addonManager.writeConfig(__name__, old_config)


config = Config()

# Create an OpenAPI Client
class OpenAIClient:
    def __init__(self, config: Config):
        self.api_key = config.openai_api_key

    def get_chat_response(self, prompt: str):
        r = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {self.api_key}",
            },
            json={"model": config.openai_model, "messages": [{"role": "user", "content": prompt}]},
        )

        resp = r.json()
        msg = resp["choices"][0]["message"]["content"]
        return msg

client = OpenAIClient(config)

def get_chat_response_in_background(prompt: str, field: str, on_success: Callable):
    if not mw:
        print("Error: mw not found")
        return

    op = QueryOp(
        parent=mw,
        op=lambda _: client.get_chat_response(prompt),
        success=lambda msg: on_success(msg, field),
    )

    op.run_in_background()

def get_prompt_fields_lower(prompt: str):
    pattern = r"\{\{(.+?)\}\}"
    fields = re.findall(pattern, prompt)
    return [field.lower() for field in fields]

# TODO: need to use this
def validate_prompt(prompt: str, note: Note):
    prompt_fields = get_prompt_fields_lower(prompt)

    all_note_fields = {field.lower(): value for field, value in note.items()}

    for prompt_field in prompt_fields:
        if prompt_field not in all_note_fields:
            return False

    return True


def interpolate_prompt(prompt: str, note: Note):
    # Bunch of extra logic to make this whole process case insensitive

    # Regex to pull out any words enclosed in double curly braces
    fields = get_prompt_fields_lower(prompt)
    pattern = r"\{\{(.+?)\}\}"

    # field.lower() -> value map
    all_note_fields = {field.lower(): value for field, value in note.items()}

    # Lowercase the characters inside {{}} in the prompt
    prompt = re.sub(pattern, lambda x: "{{" + x.group(1).lower() + "}}", prompt)

    # Sub values in prompt
    for field in fields:
        value = all_note_fields.get(field, "")
        prompt = prompt.replace("{{" + field + "}}", value)

    print("Processed prompt: ", prompt)
    return prompt

def async_process_note(note: Note, on_success: Callable, overwrite_fields=False):
    note_type = note.note_type()

    if not note_type:
        print("Error: no note type")
        return

    note_type_name = note_type["name"]
    field_prompts = config.prompts_map.get("note_types", {}).get(note_type_name, None)

    if not field_prompts:
        print("Error: no prompts found for note type")
        return

    # TODO: should run in parallel for cards that have multiple fields needing prompting.
    # Needs to be in a threadpool exec but kinda painful. Later.
    for (field, prompt) in field_prompts["fields"].items():
        # Don't overwrite fields that already exist
        if (not overwrite_fields) and note[field]:
            print(f"Skipping field: {field}")
            continue

        print(f"Processing field: {field}, prompt: {prompt}")

        prompt = interpolate_prompt(prompt, note)

        def wrapped_on_success(msg: str, target_field: str):
            note[target_field] = msg
            # Perform UI side effects
            on_success()
            print("Successfully ran in background")

        get_chat_response_in_background(prompt, field, wrapped_on_success)

def on_editor(buttons: List[str], e: editor.Editor):
    def fn(editor: editor.Editor):
        note = editor.note
        if not note:
            print("Error: no note found")
            return

        async_process_note(note=note, on_success=lambda: editor.loadNote(), overwrite_fields=True)

    button = e.addButton(cmd="Fill out stuff", func=fn, icon="!")
    buttons.append(button)

def on_review(card: Card):
    print("Reviewing...")
    note = card.note()

    def update_note():
        if not mw:
            print("Error: mw not found")
            return

        mw.col.update_note(note)
        card.load()
        print("Updated on review")

    async_process_note(note=note, on_success=update_note, overwrite_fields=False)

class AIFieldsOptionsDialog(QDialog):
    def __init__(self, config: Config):
        super().__init__()
        self.api_key_edit = None
        self.config = config

        self.setup_ui()


    def setup_ui(self):
        self.setWindowTitle("AI Fields Options")

        # Setup Widgets

        # API Key
        api_key_label = QLabel("OpenAI API Key")
        api_key_label.setToolTip("Get your API key from https://platform.openai.com/account/api-keys")
        self.api_key_edit = QLineEdit()
        self.api_key_edit.setText(config.openai_api_key)
        self.api_key_edit.setPlaceholderText("12345....")

        # Buttons Button
        # Need a restore defaults button
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Cancel | QDialogButtonBox.StandardButton.Ok)
        buttons.accepted.connect(self.on_accept)
        buttons.rejected.connect(self.on_reject)

        # Setup Layout

        # TODO: god knows if this is the right approach...
        grid = QGridLayout()
        grid.addWidget(api_key_label, 0, 0)
        grid.addWidget(self.api_key_edit, 0, 1)
        grid.addWidget(buttons, 1, 0, 1, 2)
        self.setLayout(grid)

    def on_accept(self):
        self.config.openai_api_key = self.api_key_edit.text()
        self.accept()

    def on_reject(self):
        self.reject()



def on_options():
    dialog = AIFieldsOptionsDialog(config)
    dialog.show()
    dialog.exec()

def on_main_window():
    # Add options to Anki Menu
    options_action = QAction("AI Fields Options...", mw)
    options_action.triggered.connect(on_options)
    mw.form.menuTools.addAction(options_action)

    # TODO: do I need a profile_will_close thing here?
    print("Loaded")

gui_hooks.editor_did_init_buttons.append(on_editor)
# TODO: I think this should be 'card did show'?
gui_hooks.reviewer_did_show_question.append(on_review)
gui_hooks.main_window_did_init.append(on_main_window)