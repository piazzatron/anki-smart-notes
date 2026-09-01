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

from __future__ import annotations

import asyncio
import uuid
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Literal, cast

from anki.decks import DeckId
from aqt import mw
from aqt.editor import EditorMode
from aqt.operations.note import add_note, update_note

from ..constants import GLOBAL_DECK_ID
from ..decks import deck_name_to_id_map
from ..event_bus import ActiveTargetChanged, event_bus
from ..web import dto
from ..web.dto.models import (
    AssistantAddNoteRequest,
    AssistantGetFieldRequest,
    AssistantTarget,
    AssistantTargetDto,
    AssistantUpdateFieldRequest,
)

if TYPE_CHECKING:
    from anki.cards import Card
    from anki.notes import Note
    from aqt.editor import Editor
    from aqt.qt import QWidget

EDITOR_TARGET_MODES: dict[EditorMode, Literal["add", "edit"]] = {
    EditorMode.ADD_CARDS: "add",
    EditorMode.BROWSER: "edit",
    EditorMode.EDIT_CURRENT: "edit",
}


class AssistantTargetService:
    """Owns active-target arbitration and routes assistant field operations.

    The webapp echoes plugin-minted handles without interpreting them. This
    service is therefore the only layer that maps a handle back to a review
    note or a specific live editor buffer.
    """

    def __init__(self) -> None:
        self._editor_bindings: dict[int, _EditorBinding] = {}
        self._active_handle: AssistantTargetDto | None = None

    def register_editor(self, editor: Editor) -> None:
        editor_key = id(editor)
        if editor_key in self._editor_bindings:
            return

        binding = _EditorBinding(
            editor=editor,
            buffer_id=str(uuid.uuid4()),
            note_object_id=id(editor.note) if editor.note is not None else None,
        )
        self._editor_bindings[editor_key] = binding

        # A stale buffer handle must never redirect to another editor.
        editor.parentWindow.destroyed.connect(
            lambda _object=None, key=editor_key: self.unregister_editor(key)
        )

    def unregister_editor(self, editor_key: int) -> None:
        binding = self._editor_bindings.pop(editor_key, None)
        if binding is None or self._active_handle is None:
            return
        if self._active_handle.get("bufferId") == binding.buffer_id:
            self._publish_cleared()

    def on_editor_loaded(self, editor: Editor) -> None:
        self.register_editor(editor)
        binding = self._editor_bindings[id(editor)]
        note_object_id = id(editor.note) if editor.note is not None else None
        if binding.note_object_id != note_object_id:
            binding.buffer_id = str(uuid.uuid4())
            binding.note_object_id = note_object_id

        if editor.parentWindow.isActiveWindow():
            self.activate_editor(editor)

    def on_focus_changed(self, widget: QWidget | None) -> None:
        if widget is None:
            return
        window = widget.window()

        for binding in list(self._editor_bindings.values()):
            try:
                if binding.editor.parentWindow is window:
                    self.activate_editor(binding.editor)
                    return
            except RuntimeError:
                self.unregister_editor(id(binding.editor))

        if mw and window is mw:
            card = getattr(getattr(mw, "reviewer", None), "card", None)
            if getattr(mw, "state", None) == "review" and card is not None:
                self.activate_reviewer(card)
            else:
                self._publish_cleared()

    def on_reviewer_card_changed(self, card: Card) -> None:
        if (
            self._active_handle is not None and self._active_handle["mode"] == "review"
        ) or (mw and mw.isActiveWindow()):
            self.activate_reviewer(card)

    def on_reviewer_closed(self) -> None:
        if self._active_handle is not None and self._active_handle["mode"] == "review":
            self._publish_cleared()

    def refresh_active_editor(self) -> None:
        if self._active_handle is None or self._active_handle["mode"] == "review":
            return
        binding = self._binding_for_buffer(self._active_handle["bufferId"])
        if binding is not None:
            self.activate_editor(binding.editor)

    def activate_reviewer(self, card: Card) -> None:
        handle = cast(
            AssistantTargetDto,
            {"mode": "review", "cardId": int(card.id)},
        )
        self._publish_target(handle, card.note(), int(card.did))

    def activate_editor(self, editor: Editor) -> None:
        self.register_editor(editor)
        note = editor.note
        if note is None:
            self._publish_cleared()
            return

        binding = self._editor_bindings[id(editor)]
        mode = EDITOR_TARGET_MODES[editor.editorMode]
        if mode == "add":
            handle = cast(
                AssistantTargetDto,
                {"mode": "add", "bufferId": binding.buffer_id},
            )
        else:
            handle = cast(
                AssistantTargetDto,
                {
                    "mode": "edit",
                    "noteId": int(note.id),
                    "bufferId": binding.buffer_id,
                },
            )

        self._publish_target(handle, note, _editor_deck_id(editor))

    async def get_field(self, request: AssistantGetFieldRequest) -> dict[str, str]:
        loop = asyncio.get_running_loop()
        result: asyncio.Future[dict[str, str]] = loop.create_future()

        def start() -> None:
            try:
                resolved = self._resolve_target(request.target)
                if resolved.editor is None:
                    _require_field(resolved.note, request.field_name)
                    _finish(loop, result, {"value": resolved.note[request.field_name]})
                    return

                def read_editor_buffer() -> None:
                    try:
                        current = self._resolve_target(request.target)
                        _require_field(current.note, request.field_name)
                        _finish(
                            loop,
                            result,
                            {"value": current.note[request.field_name]},
                        )
                    except Exception as error:
                        _fail(loop, result, error)

                resolved.editor.call_after_note_saved(
                    read_editor_buffer,
                    keepFocus=True,
                )
            except Exception as error:
                _fail(loop, result, error)

        self._run_on_main(loop, result, start)
        return await result

    async def update_field(
        self, request: AssistantUpdateFieldRequest
    ) -> dict[str, Any]:
        loop = asyncio.get_running_loop()
        result: asyncio.Future[dict[str, Any]] = loop.create_future()

        def start() -> None:
            try:
                main_window = mw
                if not main_window or not main_window.col:
                    raise RuntimeError("Anki collection is unavailable")
                collection = main_window.col
                resolved = self._resolve_target(request.target)
                if resolved.editor is not None:
                    resolved.editor.call_after_note_saved(
                        lambda: self._update_editor_field(loop, result, request),
                        keepFocus=True,
                    )
                    return

                _require_field(resolved.note, request.field_name)
                previous_value = resolved.note[request.field_name]
                resolved.note[request.field_name] = request.new_value

                def succeeded(_changes: object) -> None:
                    if (
                        request.target is not None
                        and request.target.card_id is not None
                    ):
                        try:
                            card = collection.get_card(request.target.card_id)
                            if self._active_handle == {
                                "mode": "review",
                                "cardId": int(request.target.card_id),
                            }:
                                self.activate_reviewer(card)
                        except Exception:
                            pass
                    _finish(
                        loop,
                        result,
                        {
                            "status": "updated",
                            "fieldName": request.field_name,
                            "previousValue": previous_value,
                            "value": request.new_value,
                        },
                    )

                update_note(parent=main_window, note=resolved.note).success(
                    succeeded
                ).failure(lambda error: _fail(loop, result, error)).run_in_background()
            except Exception as error:
                _fail(loop, result, error)

        self._run_on_main(loop, result, start)
        return await result

    async def add_note(self, request: AssistantAddNoteRequest) -> dict[str, Any]:
        loop = asyncio.get_running_loop()
        result: asyncio.Future[dict[str, Any]] = loop.create_future()

        def start() -> None:
            try:
                if not mw or not mw.col:
                    raise RuntimeError("Anki collection is unavailable")

                note_type = mw.col.models.by_name(request.note_type)
                if note_type is None:
                    valid = ", ".join(
                        sorted(str(model["name"]) for model in mw.col.models.all())
                    )
                    raise ValueError(
                        f"Unknown note type: {request.note_type}. "
                        f"Valid note types: {valid}"
                    )

                decks: dict[str, DeckId] = {
                    name: deck_id
                    for name, deck_id in deck_name_to_id_map().items()
                    if deck_id != GLOBAL_DECK_ID
                }
                decks.update(
                    {
                        item.name: DeckId(item.id)
                        for item in mw.col.decks.all_names_and_ids(
                            skip_empty_default=False
                        )
                    }
                )
                deck_id = decks.get(request.deck)
                if deck_id is None:
                    raise ValueError(
                        f"Unknown deck: {request.deck}. "
                        f"Valid decks: {', '.join(sorted(decks))}"
                    )

                note = mw.col.new_note(note_type)
                valid_fields = list(note.keys())
                unknown_fields = sorted(set(request.fields) - set(valid_fields))
                if unknown_fields:
                    raise ValueError(
                        f"Unknown fields: {', '.join(unknown_fields)}. "
                        f"Valid fields: {', '.join(valid_fields)}"
                    )
                for field_name, value in request.fields.items():
                    note[field_name] = value
                note.tags = request.tags

                def succeeded(_changes: object) -> None:
                    card_ids = [int(card_id) for card_id in note.card_ids()]
                    _finish(
                        loop,
                        result,
                        {
                            "noteId": int(note.id),
                            "cardIds": card_ids,
                            "cardCount": len(card_ids),
                        },
                    )

                add_note(parent=mw, note=note, target_deck_id=deck_id).success(
                    succeeded
                ).failure(lambda error: _fail(loop, result, error)).run_in_background()
            except Exception as error:
                _fail(loop, result, error)

        self._run_on_main(loop, result, start)
        return await result

    def _update_editor_field(
        self,
        loop: asyncio.AbstractEventLoop,
        result: asyncio.Future[dict[str, Any]],
        request: AssistantUpdateFieldRequest,
    ) -> None:
        try:
            resolved = self._resolve_target(request.target)
            if resolved.editor is None:
                raise ValueError("The editor target is stale. Ask the user to retry.")
            _require_field(resolved.note, request.field_name)
            previous_value = resolved.note[request.field_name]
            resolved.note[request.field_name] = request.new_value
            resolved.editor.loadNoteKeepingFocus()
            if self._active_handle == _target_to_dto(request.target):
                self.activate_editor(resolved.editor)
            _finish(
                loop,
                result,
                {
                    "status": "buffered",
                    "fieldName": request.field_name,
                    "previousValue": previous_value,
                    "value": request.new_value,
                    "message": "Field set in the editor; unsaved until the user saves.",
                },
            )
        except Exception as error:
            _fail(loop, result, error)

    def _resolve_target(self, target: AssistantTarget | None) -> _ResolvedTarget:
        if not mw or not mw.col:
            raise RuntimeError("Anki collection is unavailable")
        if target is None:
            raise ValueError(
                "No active target. Ask the user to focus a reviewer card or editor."
            )
        if target.mode == "review" and target.card_id is not None:
            try:
                return _ResolvedTarget(
                    note=mw.col.get_card(target.card_id).note(),
                    editor=None,
                )
            except Exception as error:
                raise ValueError(
                    "The reviewed card target is stale. Ask the user to retry."
                ) from error
        if target.buffer_id is None:
            raise ValueError("The editor target is invalid. Ask the user to retry.")

        binding = self._binding_for_buffer(target.buffer_id)
        if binding is None or binding.editor.note is None:
            raise ValueError("The editor target is stale. Ask the user to retry.")
        mode = EDITOR_TARGET_MODES[binding.editor.editorMode]
        if mode != target.mode:
            raise ValueError("The editor target is stale. Ask the user to retry.")
        if target.mode == "edit" and int(binding.editor.note.id) != target.note_id:
            raise ValueError("The editor target is stale. Ask the user to retry.")
        return _ResolvedTarget(note=binding.editor.note, editor=binding.editor)

    def _binding_for_buffer(self, buffer_id: str) -> _EditorBinding | None:
        return next(
            (
                binding
                for binding in self._editor_bindings.values()
                if binding.buffer_id == buffer_id
            ),
            None,
        )

    def _publish_target(
        self,
        handle: AssistantTargetDto,
        note: Note,
        deck_id: int | None,
    ) -> None:
        self._active_handle = handle
        event_bus.publish(
            ActiveTargetChanged(
                cast(
                    dict[str, Any],
                    dto.build_assistant_active_target(
                        handle=handle,
                        note=note,
                        deck_id=deck_id,
                        deck_name=_deck_name(deck_id),
                    ),
                )
            )
        )

    def _publish_cleared(self) -> None:
        self._active_handle = None
        event_bus.publish(
            ActiveTargetChanged(
                cast(dict[str, Any], dto.build_assistant_active_target_cleared())
            )
        )

    @staticmethod
    def _run_on_main(
        loop: asyncio.AbstractEventLoop,
        result: asyncio.Future[Any],
        callback: Any,
    ) -> None:
        if not mw:
            _fail(loop, result, RuntimeError("Anki is unavailable"))
            return
        try:
            mw.taskman.run_on_main(callback)
        except Exception as error:
            _fail(loop, result, error)


@dataclass
class _EditorBinding:
    editor: Editor
    buffer_id: str
    note_object_id: int | None


@dataclass(frozen=True)
class _ResolvedTarget:
    note: Note
    editor: Editor | None


def _editor_deck_id(editor: Editor) -> int | None:
    if editor.editorMode == EditorMode.ADD_CARDS:
        parent = cast(Any, editor.parentWindow)
        return int(parent.deck_chooser.selected_deck_id)
    if editor.card is not None:
        return int(editor.card.did)
    cards = editor.note.cards() if editor.note is not None else []
    return int(cards[0].did) if cards else None


def _deck_name(deck_id: int | None) -> str | None:
    if deck_id is None or not mw or not mw.col:
        return None
    return mw.col.decks.name_if_exists(DeckId(deck_id))


def _require_field(note: Note, field_name: str) -> None:
    field_names = list(note.keys())
    if field_name not in field_names:
        raise ValueError(
            f"Unknown field: {field_name}. Valid fields: {', '.join(field_names)}"
        )


def _target_to_dto(target: AssistantTarget | None) -> AssistantTargetDto | None:
    if target is None:
        return None
    if target.mode == "review":
        return cast(
            AssistantTargetDto,
            {"mode": "review", "cardId": int(cast(int, target.card_id))},
        )
    if target.mode == "add":
        return cast(
            AssistantTargetDto,
            {"mode": "add", "bufferId": cast(str, target.buffer_id)},
        )
    return cast(
        AssistantTargetDto,
        {
            "mode": "edit",
            "noteId": cast(int, target.note_id),
            "bufferId": cast(str, target.buffer_id),
        },
    )


def _finish(
    loop: asyncio.AbstractEventLoop,
    future: asyncio.Future[Any],
    value: Any,
) -> None:
    loop.call_soon_threadsafe(_set_future_result, future, value)


def _fail(
    loop: asyncio.AbstractEventLoop,
    future: asyncio.Future[Any],
    error: BaseException,
) -> None:
    loop.call_soon_threadsafe(_set_future_exception, future, error)


def _set_future_result(future: asyncio.Future[Any], value: Any) -> None:
    if not future.done():
        future.set_result(value)


def _set_future_exception(future: asyncio.Future[Any], error: BaseException) -> None:
    if not future.done():
        future.set_exception(error)


assistant_target_service = AssistantTargetService()
