from typing import List, Callable, TypedDict, Dict, Union, Any
import re
import sys
import os
from aqt import gui_hooks, editor, mw, browser
from aqt.operations import QueryOp, CollectionOp
from anki.cards import Card
from anki.notes import Note
from anki.collection import OpChanges
from aqt.qt import (
    QAction,
    QDialog,
    QLabel,
    QLineEdit,
    QDialogButtonBox,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QFormLayout,
    QPushButton,
    QHBoxLayout,
    QComboBox,
    QTextEdit,
    QTextOption,
    QMenu,
    QMessageBox,
)
from PyQt6.QtCore import Qt

# TODO: sort imports...

# Nonsense to allow importing from site-packages
# TODO: need to explicitly vendor here...
packages_dir = os.path.join(
    os.path.dirname(os.path.realpath(__file__)), "env/lib/python3.11/site-packages"
)
print(packages_dir)
sys.path.append(packages_dir)

import aiohttp
import asyncio


def run_async_in_background(op: Callable, on_success: Callable):
    "Runs an async operation in the background and calls on_success when done."

    if not mw:
        raise Exception("Error: mw not found in run_async_in_background")

    query_op = QueryOp(
        parent=mw,
        op=lambda _: asyncio.run(op()),
        success=on_success,
    )

    query_op.run_in_background()


class NoteTypeMap(TypedDict):
    fields: Dict[str, str]


class PromptMap(TypedDict):
    note_types: Dict[str, NoteTypeMap]


class Config:
    openai_api_key: str
    prompts_map: PromptMap
    openai_model: str  # TODO: type this

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

    def get_prompt(self, note_type: str, field: str):
        return (
            self.prompts_map.get("note_types", {})
            .get(note_type, {"fields": {}})
            .get("fields", {})
            .get(field, None)
        )


config = Config()


def check_for_api_key(show_box=True):
    if not config.openai_api_key:
        if show_box:
            message = "No OpenAI API key found. Please enter your API key in the options menu."
            show_message_box(message)
        return False
    return True


# Create an OpenAPI Client
class OpenAIClient:
    def __init__(self, config: Config):
        self.api_key = config.openai_api_key

    async def async_get_chat_response(self, prompt: str):
        async with aiohttp.ClientSession() as session:
            async with session.post(
                "https://api.openai.com/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                },
                json={
                    "model": config.openai_model,
                    "messages": [{"role": "user", "content": prompt}],
                },
            ) as response:
                resp = await response.json()
                msg = resp["choices"][0]["message"]["content"]
                return msg


client = OpenAIClient(config)


def get_prompt_fields_lower(prompt: str):
    pattern = r"\{\{(.+?)\}\}"
    fields = re.findall(pattern, prompt)
    return [field.lower() for field in fields]


def get_fields(note_type: str):
    if not mw or not mw.col:
        return []

    if not note_type:
        return []

    model = mw.col.models.by_name(note_type)
    if not model:
        return []

    return [field["name"] for field in model["flds"]]


def validate_prompt(prompt: str, note_type: str, target_field: Union[str, None] = None):
    fields = {field.lower() for field in get_fields(note_type)}
    prompt_fields = get_prompt_fields_lower(prompt)

    # Check for fields that aren't in the card
    for prompt_field in prompt_fields:
        if prompt_field not in fields:
            return False

    # Can't reference itself
    if target_field and target_field.lower() in prompt_fields:
        return False

    return True


def interpolate_prompt(prompt: str, note: Note):
    # Bunch of extra logic to make this whole process case insensitive

    # Regex to pull out any words enclosed in double curly braces
    fields = get_prompt_fields_lower(prompt)
    pattern = r"\{\{(.+?)\}\}"

    # field.lower() -> value map
    all_note_fields = to_lowercase_dict(note)

    # Lowercase the characters inside {{}} in the prompt
    prompt = re.sub(pattern, lambda x: "{{" + x.group(1).lower() + "}}", prompt)

    # Sub values in prompt
    for field in fields:
        value = all_note_fields.get(field, "")
        prompt = prompt.replace("{{" + field + "}}", value)

    print("Processed prompt: ", prompt)
    return prompt


async def process_notes(notes: List[Note]):
    tasks = []
    for note in notes:
        tasks.append(process_note(note))
    await asyncio.gather(*tasks)


def process_notes_with_progress(note_ids: List[int]):
    """Processes notes in the background with a progress bar, batching into a single undo op"""
    print("Processing notes...")
    if not check_for_api_key():
        return

    if not mw:
        return

    def wrapped_process_notes():
        notes = [mw.col.get_note(note_id) for note_id in note_ids]
        asyncio.run(process_notes(notes))
        changes = OpChanges()
        changes.note = True
        mw.col.update_notes(notes)
        return changes

    op = CollectionOp(
        parent=mw,
        op=lambda _: wrapped_process_notes(),
    )

    op.run_in_background()


async def process_note(note: Note, overwrite_fields=False):
    print(f"Processing note")
    note_type = note.note_type()

    if not note_type:
        print("Error: no note type")
        return

    note_type_name = note_type["name"]
    field_prompts = config.prompts_map.get("note_types", {}).get(note_type_name, None)

    if not field_prompts:
        print("Error: no prompts found for note type")
        return

    tasks = []

    field_prompt_items = list(field_prompts["fields"].items())
    for field, prompt in field_prompt_items:
        # Don't overwrite fields that already exist
        if (not overwrite_fields) and note[field]:
            print(f"Skipping field: {field}")
            continue

        print(f"Processing field: {field}, prompt: {prompt}")

        prompt = interpolate_prompt(prompt, note)

        task = client.async_get_chat_response(prompt)
        tasks.append(task)

    # Maybe filled out already, if so return early
    if not tasks:
        return

    # TODO: handle exceptions here
    responses = await asyncio.gather(*tasks)
    print("Responses: ", responses)
    for i, response in enumerate(responses):
        target_field = field_prompt_items[i][0]
        note[target_field] = response


def add_editor_top_button(buttons: List[str], e: editor.Editor):
    def fn(editor: editor.Editor):
        if not check_for_api_key():
            return

        note = editor.note

        if not note:
            print("Error: no note found")
            return

        if not mw:
            return

        def on_success():
            print("ON SUCCESS ID")
            print(note.id)

            # New notes have note id 0
            if note.id:
                # Only update note if it's already in the database
                mw.col.update_note(note)
            editor.loadNote()

        run_async_in_background(
            lambda: process_note(note, overwrite_fields=True), lambda _: on_success()
        )

    button = e.addButton(
        cmd="AI Generate Fields",
        label="✨",
        func=fn,
        icon=None,
        tip="AI Generate Fields",
    )

    buttons.append(button)


def on_review(card: Card):
    print("Reviewing...")
    if not check_for_api_key(show_box=False):
        return
    note = card.note()

    def on_success():
        if not mw:
            print("Error: mw not found")
            return

        mw.col.update_note(note)
        card.load()
        print("Updated on review")

    run_async_in_background(
        lambda: process_note(note, overwrite_fields=False),
        on_success=lambda x: on_success(),
    )


def show_message_box(
    message: str,
    details: Union[str, None] = None,
    custom_ok: Union[str, None] = None,
    show_cancel: bool = False,
):
    msg = QMessageBox()
    msg.setText(message)

    if details:
        msg.setInformativeText(details)

    # TODO: this custom_ok is getting put in the wrong position (left most), idk why
    ok_button = None
    if custom_ok:
        ok_button = QPushButton(custom_ok)
        msg.addButton(ok_button, QMessageBox.ButtonRole.ActionRole)

    else:
        msg.addButton(QMessageBox.StandardButton.Ok)

    if show_cancel:
        msg.addButton(QMessageBox.StandardButton.Cancel)

    val = msg.exec()
    return msg.clickedButton() == ok_button or val == QMessageBox.StandardButton.Ok


openai_models = ["gpt-3.5-turbo", "gpt-4o", "gpt-4-turbo", "gpt-4"]

OPTIONS_MIN_WIDTH = 750


class AIFieldsOptionsDialog(QDialog):
    def __init__(self, config: Config):
        super().__init__()
        self.api_key_edit = None
        self.prompts_map = config.prompts_map
        self.openai_model = config.openai_model
        self.remove_button = None
        self.table = None
        self.config = config
        self.selected_row = None
        self.model_combo_box = None

        self.setup_ui()

    def setup_ui(self):
        self.setWindowTitle("🤖 AI Fields Options")
        self.setMinimumWidth(OPTIONS_MIN_WIDTH)

        # Setup Widgets

        # Form
        api_key_label = QLabel("OpenAI API Key")
        api_key_label.setToolTip(
            "Get your API key from https://platform.openai.com/account/api-keys"
        )

        self.api_key_edit = QLineEdit()
        self.api_key_edit.setText(config.openai_api_key)
        self.api_key_edit.setPlaceholderText("sk-proj-1234...")

        # Select model
        model_label = QLabel("OpenAI Model")
        self.models_combo_box = QComboBox()
        self.models_combo_box.addItems(openai_models)
        self.models_combo_box.setCurrentText(self.openai_model)
        self.models_combo_box.currentTextChanged.connect(self.on_change_model)

        form = QFormLayout()
        form.addRow(api_key_label, self.api_key_edit)
        form.addRow(model_label, self.models_combo_box)

        # Buttons
        # TODO: Need a restore defaults button
        table_buttons = QHBoxLayout()
        add_button = QPushButton("+")
        add_button.clicked.connect(self.on_add)
        self.remove_button = QPushButton("-")
        table_buttons.addWidget(self.remove_button)
        self.remove_button.clicked.connect(self.on_remove)
        table_buttons.addWidget(add_button)

        standard_buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Cancel | QDialogButtonBox.StandardButton.Ok
        )

        standard_buttons.accepted.connect(self.on_accept)
        standard_buttons.rejected.connect(self.on_reject)

        # Table
        self.table = self.create_table()
        self.update_table()

        # Set up layout

        layout = QVBoxLayout()
        layout.addLayout(form)
        layout.addWidget(self.table)
        layout.addLayout(table_buttons)
        layout.addWidget(standard_buttons)

        self.update_buttons()
        self.setLayout(layout)

    def create_table(self):
        table = QTableWidget(0, 3)
        table.setHorizontalHeaderLabels(["Note Type", "Field", "Prompt"])

        # Selection
        table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)

        # Styling
        table.horizontalHeader().setStretchLastSection(True)
        table.verticalHeader().setVisible(False)

        # Wire up slots
        table.currentItemChanged.connect(self.on_row_selected)
        table.itemDoubleClicked.connect(self.on_row_double_clicked)

        return table

    def update_table(self):
        self.table.setRowCount(0)

        row = 0
        for note_type, field_prompts in self.prompts_map["note_types"].items():
            for field, prompt in field_prompts["fields"].items():
                print(field, prompt)
                self.table.insertRow(self.table.rowCount())
                items = [
                    QTableWidgetItem(note_type),
                    QTableWidgetItem(field),
                    QTableWidgetItem(prompt),
                ]
                for i, item in enumerate(items):
                    item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                    self.table.setItem(row, i, item)
                row += 1

    def on_row_selected(self, current):
        if not current:
            self.selected_row = None
        else:
            self.selected_row = current.row()
        self.update_buttons()

    def on_row_double_clicked(self, item):
        print(f"Double clicked: {item.row()}")
        card_type = self.table.item(self.selected_row, 0).text()
        field = self.table.item(self.selected_row, 1).text()
        prompt = self.table.item(self.selected_row, 2).text()
        print(f"Editing {card_type}, {field}")
        prompt_dialog = QPromptDialog(
            self.prompts_map,
            self.on_update_prompts,
            card_type=card_type,
            field=field,
            prompt=prompt,
        )

        if prompt_dialog.exec() == QDialog.DialogCode.Accepted:
            self.update_table()

    def update_buttons(self):
        if self.selected_row is not None:
            self.remove_button.setEnabled(True)
        else:
            self.remove_button.setEnabled(False)

    def on_add(self, row):
        print(row)
        prompt_dialog = QPromptDialog(self.prompts_map, self.on_update_prompts)
        if prompt_dialog.exec() == QDialog.DialogCode.Accepted:
            self.update_table()

    def on_remove(self):
        if self.selected_row is None:
            # Should never happen
            return
        card_type = self.table.item(self.selected_row, 0).text()
        field = self.table.item(self.selected_row, 1).text()
        print(f"Removing {card_type}, {field}")
        self.prompts_map["note_types"][card_type]["fields"].pop(field)
        self.update_table()

    def on_change_model(self, text: str):
        if self.openai_model == "gpt-3.5-turbo" and text and text != self.openai_model:
            warning = f"Continue with {text}?"
            informative = "Only paid API tiers can use models other than gpt-3.5-turbo."

            should_continue = show_message_box(
                warning, details=informative, show_cancel=True
            )

            if should_continue:
                self.openai_model = text
            else:
                # Otherwise, reset the combo box
                self.models_combo_box.setCurrentText(self.openai_model)

        else:
            self.openai_model = text

    def on_accept(self):
        self.config.openai_api_key = self.api_key_edit.text()
        self.config.prompts_map = self.prompts_map
        self.config.openai_model = self.openai_model
        self.accept()

    def on_reject(self):
        self.reject()

    def on_update_prompts(self, prompts_map: PromptMap):
        self.prompts_map = prompts_map


class QPromptDialog(QDialog):
    def __init__(
        self,
        prompts_map: Config,
        on_accept_callback: Callable,
        card_type: Union[str, None] = None,
        field: Union[str, None] = None,
        prompt: Union[str, None] = None,
    ):
        super().__init__()
        self.config = config
        self.on_accept_callback = on_accept_callback
        self.prompts_map = prompts_map

        self.card_types = self.get_card_types()
        self.selected_card_type = card_type or self.card_types[0]

        self.fields = get_fields(self.selected_card_type)
        self.selected_field = field or get_fields(self.selected_card_type)[0]

        self.prompt = prompt
        self.prompt_text_box = None
        self.is_loading_prompt = False
        self.field_combo_box = None
        self.test_button = None

        self.setup_ui()

    def setup_ui(self):
        self.setWindowTitle("Set Prompt")
        card_combo_box = QComboBox()

        self.field_combo_box = QComboBox()

        card_combo_box.addItems(self.card_types)

        card_combo_box.setCurrentText(self.selected_card_type)
        card_combo_box.currentTextChanged.connect(self.on_card_type_selected)

        card_label = QLabel("Card Type")
        field_label = QLabel("Target Field")
        layout = QVBoxLayout()
        layout.addWidget(card_label)
        layout.addWidget(card_combo_box)
        layout.addWidget(field_label)
        layout.addWidget(self.field_combo_box)

        standard_buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Cancel
            | QDialogButtonBox.StandardButton.Save
        )

        self.test_button = QPushButton("Test Prompt 🤖")
        self.test_button.clicked.connect(self.on_test)
        standard_buttons.accepted.connect(self.on_accept)
        standard_buttons.rejected.connect(self.on_reject)

        prompt_label = QLabel("Prompt")
        self.prompt_text_box = QTextEdit()
        self.prompt_text_box.textChanged.connect(self.on_text_changed)
        self.prompt_text_box.setMinimumHeight(150)
        self.prompt_text_box.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.prompt_text_box.setLineWrapMode(QTextEdit.LineWrapMode.WidgetWidth)
        self.prompt_text_box.setWordWrapMode(
            QTextOption.WrapMode.WrapAtWordBoundaryOrAnywhere
        )
        # TODO: why isn't placeholder showing up?
        self.prompt_text_box.setPlaceholderText(
            "Create an example sentence in Japanese for the word {{expression}}. Use only simple grammar and vocab. Respond only with the Japanese example sentence."
        )

        self.update_prompt()
        self.setLayout(layout)
        layout.addWidget(prompt_label)
        layout.addWidget(self.prompt_text_box)
        layout.addWidget(self.test_button)
        layout.addWidget(standard_buttons)

        self.update_test_button()
        # This needs to be called at the end
        # once the widgets are set up
        self.update_fields()
        # Very brittle; this needs to be called after update_fields
        # because otherwise update_fields will clear out the field combo box,
        # causing it to default select the first field in the list
        self.field_combo_box.currentTextChanged.connect(self.on_field_selected)

    def get_card_types(self):
        # Including this function in a little UI
        # class is a horrible violation of separation of concerns
        # but I won't tell anybody if you don't

        models = mw.col.models.all()
        return [model["name"] for model in models]

    def on_field_selected(self, field: str):
        print(f"Field selected: {field}")
        if not field:
            return
        self.selected_field = field
        self.update_prompt()

    def on_card_type_selected(self, card_type: str):
        if not card_type:
            return
        self.selected_card_type = card_type

        self.update_fields()
        self.update_prompt()

    def update_fields(self):
        if not self.selected_card_type:
            return

        self.fields = get_fields(self.selected_card_type)

        self.field_combo_box.clear()
        self.field_combo_box.addItems(self.fields)
        print(f"Attempting to set field to {self.selected_field}")
        self.field_combo_box.setCurrentText(self.selected_field)

    def update_test_button(self):
        is_enabled = (
            bool(self.selected_card_type and self.selected_field and self.prompt)
            and not self.is_loading_prompt
        )
        self.test_button.setEnabled(is_enabled)
        if self.is_loading_prompt:
            self.test_button.setText("Loading...")
        else:
            self.test_button.setText("Test Prompt 🤖")

    def update_prompt(self):
        if not self.selected_field or not self.selected_card_type:
            self.prompt_text_box.setText("")
            return

        prompt = (
            self.prompts_map.get("note_types", {})
            .get(self.selected_card_type, {})
            .get("fields", {})
            .get(self.selected_field, "")
        )
        self.prompt_text_box.setText(prompt)

    def on_text_changed(self):
        self.prompt = self.prompt_text_box.toPlainText()
        self.update_test_button()

    def on_test(self):
        if self.selected_card_type and self.selected_field and self.prompt:
            if not validate_prompt(self.prompt, self.selected_card_type):
                show_message_box("Invalid prompt. Please ensure all fields are valid.")
                return

        sample_note_ids = mw.col.find_notes(f'note:"{self.selected_card_type}"')

        if not sample_note_ids:
            show_message_box("No cards found for this note type.")
            return

        sample_note = mw.col.get_note(sample_note_ids[0])
        prompt = interpolate_prompt(self.prompt, sample_note)
        self.is_loading_prompt = True
        self.update_test_button()

        def on_success(arg):
            self.is_loading_prompt = False
            self.update_test_button()

            prompt_fields = get_prompt_fields_lower(self.prompt)

            # clumsy stuff to make it work with lowercase fields...
            fields = to_lowercase_dict(sample_note)
            field_map = {
                prompt_field: fields[prompt_field] for prompt_field in prompt_fields
            }

            stringified_vals = "\n".join([f"{k}: {v}" for k, v in field_map.items()])
            msg = f"Ran with fields: \n{stringified_vals}.\n\n Response: {arg}"

            show_message_box(msg, custom_ok="Close")

        run_async_in_background(
            lambda: client.async_get_chat_response(prompt), on_success
        )

    def on_accept(self):
        if self.selected_card_type and self.selected_field and self.prompt:
            if not validate_prompt(
                self.prompt, self.selected_card_type, self.selected_field
            ):
                show_message_box(
                    "Invalid prompt. Please ensure all fields are valid and do not reference the target field."
                )
                return

            # IDK if this is gonna work on the config object? I think not...
            print(
                f"Trying to set prompt for {self.selected_card_type}, {self.selected_field}, {self.prompt}"
            )
            if not self.prompts_map["note_types"].get(self.selected_card_type):
                self.prompts_map["note_types"][self.selected_card_type] = {"fields": {}}
            self.prompts_map["note_types"][self.selected_card_type]["fields"][
                self.selected_field
            ] = self.prompt
            self.on_accept_callback(self.prompts_map)
        self.accept()

    def on_reject(self):
        self.reject()


def on_options():
    dialog = AIFieldsOptionsDialog(config)
    dialog.exec()


def on_browser_context(browser: browser.Browser, menu: QMenu):
    item = QAction("Process AI Fields", menu)
    menu.addAction(item)
    item.triggered.connect(
        lambda: process_notes_with_progress(browser.selected_notes())
    )


def to_lowercase_dict(d: Dict[str, Any]):
    """Converts a dictionary to lowercase keys"""
    return {k.lower(): v for k, v in d.items()}


def is_ai_field(current_field_num: int, note: Note):
    """Helper to determine if the current field is an AI field. Returns the non-lowercased field name if it is."""
    if not note:
        return None
    note_type = note.note_type()
    # Sort dem fields and get their names
    sorted_fields = [
        field["name"] for field in sorted(note_type["flds"], key=lambda x: x["ord"])
    ]
    sorted_fields_lower = [field.lower() for field in sorted_fields]

    if not note_type or not current_field_num:
        return None

    current_field = sorted_fields_lower[current_field_num]
    print(current_field)

    prompts = config.prompts_map
    print(prompts)

    # TODO: some methods to work with this stupid note_types map
    prompts_for_card = to_lowercase_dict(
        (prompts["note_types"].get(note_type["name"], {"fields": {}}).get("fields", {}))
    )

    print(prompts_for_card)

    is_ai = bool(prompts_for_card.get(current_field, None))
    return sorted_fields[current_field_num] if is_ai else None


async def async_process_single_field(note: Note, target_field_name: str):
    print("IN PROCESS SINGLE FIELD")
    prompt = config.get_prompt(note.note_type()["name"], target_field_name)
    prompt = interpolate_prompt(prompt, note)
    response = await client.async_get_chat_response(prompt)
    note[target_field_name] = response


def process_single_field(note: Note, target_field_name: str, editor: editor.Editor):
    def on_success():
        # Only update note if it's already in the database
        if note.id:
            mw.col.update_note(note)
        editor.loadNote()

    run_async_in_background(
        lambda: async_process_single_field(note, target_field_name),
        lambda _: on_success(),
    )


def on_editor_context(editor_web_view: editor.EditorWebView, menu: QMenu):
    editor = editor_web_view.editor
    note = editor.note
    if not note:
        return

    current_field_num = editor.currentField
    if current_field_num is None:
        return

    ai_field = is_ai_field(current_field_num, note)
    print(ai_field)
    if not ai_field:
        return
    item = QAction("✨ Generate AI Field", menu)
    item.triggered.connect(lambda: process_single_field(note, ai_field, editor))
    menu.addAction(item)


def on_main_window():
    # Add options to Anki Menu
    options_action = QAction("AI Fields Options...", mw)
    options_action.triggered.connect(on_options)
    mw.form.menuTools.addAction(options_action)

    # TODO: do I need a profile_will_close thing here?


gui_hooks.browser_will_show_context_menu.append(on_browser_context)
gui_hooks.editor_did_init_buttons.append(add_editor_top_button)
gui_hooks.editor_will_show_context_menu.append(on_editor_context)
# TODO: I think this should be 'card did show'?
gui_hooks.reviewer_did_show_question.append(on_review)
gui_hooks.main_window_did_init.append(on_main_window)
