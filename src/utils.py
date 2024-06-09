from typing import Callable, Dict, Any
from aqt import mw, QDialog, QLabel
from aqt.operations import QueryOp
from .config import config

from .ui.rate_dialog import RateDialog
from .ui.ui_utils import show_message_box
import asyncio


def to_lowercase_dict(d: Dict[str, Any]) -> Dict[str, Any]:
    """Converts a dictionary to lowercase keys"""
    return {k.lower(): v for k, v in d.items()}


def get_fields(note_type: str):
    """Gets the fields of a note type."""
    if not mw or not mw.col:
        return []

    if not note_type:
        return []

    model = mw.col.models.by_name(note_type)
    if not model:
        return []

    return [field["name"] for field in model["flds"]]


def run_async_in_background(op: Callable[[], Any], on_success: Callable[[Any], None]):
    "Runs an async operation in the background and calls on_success when done."

    if not mw:
        raise Exception("Error: mw not found in run_async_in_background")

    query_op = QueryOp(
        parent=mw,
        op=lambda _: asyncio.run(op()),
        success=on_success,
    )

    query_op.run_in_background()


def check_for_api_key(show_box=True) -> bool:
    if not config.openai_api_key:
        if show_box:
            message = "No OpenAI API key found. Please enter your API key in the options menu."
            show_message_box(message)
        return False
    return True


USES_BEFORE_RATE_DIALOG = 5


def bump_usage_counter() -> None:
    config.times_used += 1
    print("Times used: ", config.times_used)
    print("Last rate dialog: ", config.last_show_rate_dialog)
    if config.times_used > USES_BEFORE_RATE_DIALOG and not config.did_show_rate_dialog:
        config.did_show_rate_dialog = True
        dialog = RateDialog()
        dialog.exec()
