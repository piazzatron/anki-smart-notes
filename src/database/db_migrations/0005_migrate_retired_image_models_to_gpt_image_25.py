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

from yoyo import step

# GPT Image 1.5 shuts down 2026-12-01; GPT Image 2 and Flux Dev are retired from the
# picker. Every one of them moves to plain GPT Image 2.5 at low quality.
RETIRED_IMAGE_MODELS = (
    "'gpt-image-1.5-low', 'gpt-image-1.5-medium', "
    "'gpt-image-2-low', 'gpt-image-2-medium', 'flux-dev'"
)

steps = [
    step(
        f"""
        UPDATE default_image_generation_settings
        SET provider = 'openai', model = 'gpt-image-2.5-flare-low'
        WHERE model IN ({RETIRED_IMAGE_MODELS});
        """,
        "SELECT 1;",
    ),
    step(
        f"""
        UPDATE image_smart_field_settings
        SET provider = 'openai', model = 'gpt-image-2.5-flare-low'
        WHERE uses_default_generation_settings = 0
            AND model IN ({RETIRED_IMAGE_MODELS});
        """,
        "SELECT 1;",
    ),
]
