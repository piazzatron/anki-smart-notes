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

from typing import List, Union

from anki.decks import DeckId
from attr import dataclass

from .models import SmartFieldType

# Had to put this in a separate field to resolve circular import btwn processor + field_resolver


@dataclass(repr=False)
class FieldNode:
    field: str
    field_upper: str
    existing_value: Union[str, None]
    out_nodes: List["FieldNode"]
    in_nodes: List["FieldNode"]
    manual: bool
    overwrite: bool
    deck_id: DeckId
    input: str
    field_type: SmartFieldType
    is_target: bool = False
    generate_despite_manual: bool = False  # Used if it's pre a target field
    did_update: bool = False

    abort = False

    def __str__(self):
        return f"Node(field={self.field}, in_nodes={[n.field for n in self.in_nodes]}, out_nodes={[n.field for n in self.out_nodes]}, manual={self.manual}, overwrite={self.overwrite}, generate_despite_manual={self.generate_despite_manual}, is_target={self.is_target}, did_update={self.did_update}"

    __repr__ = __str__
