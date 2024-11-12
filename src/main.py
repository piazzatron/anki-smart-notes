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

from .chat_provider import ChatProvider
from .config import config
from .field_processor import FieldProcessor
from .hooks import setup_hooks
from .image_provider import ImageProvider
from .note_proccessor import NoteProcessor
from .open_ai_client import OpenAIClient
from .tts_provider import TTSProvider


def main() -> None:
    openai_provider = OpenAIClient()
    chat_provider = ChatProvider()
    tts_provider = TTSProvider()
    image_provider = ImageProvider()

    field_processor = FieldProcessor(
        openai_provider=openai_provider,
        chat_provider=chat_provider,
        tts_provider=tts_provider,
        image_provider=image_provider,
    )

    processor = NoteProcessor(field_processor=field_processor, config=config)

    setup_hooks(processor)
