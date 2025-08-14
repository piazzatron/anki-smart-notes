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

from .api_client import api
from .constants import IMAGE_PROVIDER_TIMEOUT_SEC
from .models import ImageModels, ImageProviders


class ImageProvider:
    async def async_get_image_response(
        self, prompt: str, model: ImageModels, provider: ImageProviders, note_id: int
    ) -> bytes:
        response = await api.get_api_response(
            path="image",
            args={"provider": provider, "model": model, "prompt": prompt},
            note_id=note_id,
            timeout_sec=IMAGE_PROVIDER_TIMEOUT_SEC,
        )

        return response._body  # type: ignore


image_provider = ImageProvider()
