"""
Copyright (C) 2024 Michael Piazza

This file is part of Smart Notes.

Smart Notes is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

Smart Notes is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with Smart Notes.  If not, see <https://www.gnu.org/licenses/>.
"""

from collections.abc import Callable
from typing import Optional

from anki.cards import Card
from aqt import QAction, QMenu, browser, editor, mw

from ..app_state import is_capacity_remaining_or_legacy
from ..note_proccessor import NoteProcessor
from .custom_prompt import CustomImagePrompt, CustomTextPrompt, CustomTTSPrompt


class FieldMenu:
    """Constructs and attaches context menu for an editor field."""

    def __init__(
        self,
        *,
        editor_instance: editor.Editor,
        menu: QMenu,
        processor: NoteProcessor,
        card: Card,
        field_upper: str,
        is_smart_field: bool,
    ) -> None:
        self.editor = editor_instance
        self.menu = menu
        self.processor = processor
        self.card = card
        self.field_upper = field_upper
        self.is_smart_field = is_smart_field

        self._build_menu()

    # ---------------------------------------------------------------------
    # Menu construction helpers
    # ---------------------------------------------------------------------

    def _build_menu(self) -> None:
        self.menu.addSeparator()

        if self.is_smart_field:
            self._add_generate_field_action()
            self.menu.addSeparator()

        self._add_custom_actions()

    # ------------------------------------------------------------------
    # Generate Smart Field
    # ------------------------------------------------------------------

    def _add_generate_field_action(self) -> None:
        generate_item = QAction("✨ Generate Smart Field", self.menu)

        def wrapped() -> None:
            if not is_capacity_remaining_or_legacy(show_box=True):
                return

            def on_success(_: bool):
                self.editor.loadNote()

                parent = self.editor.parentWindow
                if isinstance(parent, browser.Browser) and getattr(  # type: ignore
                    parent, "_previewer", None
                ):  # type: ignore
                    parent._previewer.render_card()  # type: ignore

            self.processor.process_card(
                self.card,
                overwrite_fields=False,
                target_field=self.field_upper,
                on_success=on_success,
                show_progress=True,
            )

        generate_item.triggered.connect(wrapped)
        self.menu.addAction(generate_item)

    # ------------------------------------------------------------------
    # Custom prompt helpers
    # ------------------------------------------------------------------

    def _add_custom_actions(self) -> None:
        text_item = QAction("💬 Custom Text", self.menu)
        tts_item = QAction("📣 Custom TTS", self.menu)
        image_item = QAction("🖼️ Custom Image", self.menu)

        text_item.triggered.connect(self._on_custom_text)
        tts_item.triggered.connect(self._on_custom_tts)
        image_item.triggered.connect(self._on_custom_image)

        self.menu.addAction(text_item)
        self.menu.addAction(tts_item)
        self.menu.addAction(image_item)

    # --------------------- callbacks ----------------------------

    def _make_custom_field_success(self) -> Callable[[Optional[str]], None]:
        def _on_success(res: Optional[str]) -> None:
            if res is None:
                return

            note = self.card.note()
            note[self.field_upper] = res

            # Persist only if already in collection
            if note.id:
                mw.col.update_note(note)  # type: ignore

            self.editor.loadNote()

            parent = self.editor.parentWindow
            if isinstance(parent, browser.Browser) and getattr(  # type: ignore
                parent, "_previewer", None
            ):  # type: ignore
                parent._previewer.render_card()  # type: ignore

        return _on_success

    def _on_custom_text(self, _: bool) -> None:
        CustomTextPrompt(
            note=self.card.note(),
            deck_id=self.card.did,
            field_upper=self.field_upper,
            on_success=self._make_custom_field_success(),
        ).exec()

    def _on_custom_image(self, _: bool) -> None:
        # This should be called with exec instead of show, but
        # for some reason having a webview inside of this dialog
        # causes UI bugs when using exec
        CustomImagePrompt(
            note=self.card.note(),
            deck_id=self.card.did,
            field_upper=self.field_upper,
            on_success=self._make_custom_field_success(),
            parent=self.editor.parentWindow,
        ).show()

    def _on_custom_tts(self, _: bool) -> None:
        CustomTTSPrompt(
            note=self.card.note(),
            deck_id=self.card.did,
            field_upper=self.field_upper,
            on_success=self._make_custom_field_success(),
        ).exec()
