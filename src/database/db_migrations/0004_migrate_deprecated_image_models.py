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

steps = [
    step(
        """
        UPDATE default_image_generation_settings
        SET provider = 'replicate', model = 'z-image-turbo'
        WHERE model = 'flux-schnell';
        """,
        "SELECT 1;",
    ),
    step(
        """
        UPDATE image_smart_field_settings
        SET provider = 'replicate', model = 'z-image-turbo'
        WHERE uses_default_generation_settings = 0
            AND model = 'flux-schnell';
        """,
        "SELECT 1;",
    ),
]
