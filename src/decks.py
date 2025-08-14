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

from typing import cast

from anki.decks import DeckId, DeckTreeNode
from aqt import mw

from .constants import GLOBAL_DECK_ID, GLOBAL_DECK_NAME
from .logger import logger

cached_leaf_decks: dict[DeckId, str] = {}


# Slow af even with just a handful of decks, so cached and run off the main thread initially in hooks
# Theoretically probably a race condition


def deck_id_to_name_map() -> dict[DeckId, str]:
    global cached_leaf_decks

    if not mw or not mw.col:
        return {}

    if not len(cached_leaf_decks):
        leaves: list[DeckTreeNode] = []
        nodes = [mw.col.decks.deck_tree()]

        # Find the leaves of the deck tree
        while nodes:
            node = nodes.pop()
            if node.children:
                for child in node.children:
                    nodes.append(child)
            else:
                leaves.append(node)

        cached_leaf_decks = {cast(DeckId, node.deck_id): node.name for node in leaves}
        cached_leaf_decks[GLOBAL_DECK_ID] = GLOBAL_DECK_NAME
        logger.debug("Cached leaf decks map")
        logger.debug(cached_leaf_decks)

    return cached_leaf_decks


def deck_name_to_id_map() -> dict[str, DeckId]:
    return {v: k for k, v in deck_id_to_name_map().items()}


def get_all_deck_ids() -> list[DeckId]:
    decks_map = deck_id_to_name_map().copy()
    decks_map.pop(GLOBAL_DECK_ID)
    return [GLOBAL_DECK_ID] + sorted(decks_map.keys())
