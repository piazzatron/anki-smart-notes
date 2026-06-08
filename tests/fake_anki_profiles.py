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

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

import pytest


@dataclass(frozen=True)
class FakeProfileData:
    note_types: dict[str, int]
    deck_ids: set[int]


def profile_data(note_types: dict[str, int], deck_ids: set[int]) -> FakeProfileData:
    return FakeProfileData(note_types=note_types, deck_ids=deck_ids)


def install_fake_profile_collections(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    *,
    profiles: dict[str, FakeProfileData],
    current_profile: str = "__test__",
    addon_manager: Optional[object] = None,
    modules_with_mw: tuple[Any, ...] = (),
    modules_with_collection: tuple[Any, ...] = (),
) -> Any:
    class FakeModels:
        def __init__(self, note_types: dict[str, int]) -> None:
            self.note_types = note_types

        def all(self) -> list[dict[str, Any]]:
            return [
                {"name": name, "id": note_type_id}
                for name, note_type_id in self.note_types.items()
            ]

        def by_name(self, note_type: str) -> Optional[dict[str, Any]]:
            if note_type not in self.note_types:
                return None
            return {"name": note_type, "id": self.note_types[note_type]}

    class FakeDecks:
        def __init__(self, deck_ids: set[int]) -> None:
            self.deck_ids = deck_ids

        def all(self) -> list[dict[str, Any]]:
            return [
                {"id": deck_id, "name": f"Deck {deck_id}"}
                for deck_id in sorted(self.deck_ids)
            ]

    class FakeCollection:
        def __init__(self, profile_name: str) -> None:
            data = profiles[profile_name]
            self.models = FakeModels(data.note_types)
            self.decks = FakeDecks(data.deck_ids)
            self.did_close = False

        def close(self) -> None:
            self.did_close = True

    class FakeProfileManager:
        name = current_profile
        base = str(tmp_path / "profiles")

        def profiles(self) -> list[str]:
            return list(profiles)

    class FakeMw:
        def __init__(self) -> None:
            self.pm = FakeProfileManager()
            self.col = FakeCollection(current_profile)
            self.opened_collections: list[FakeCollection] = []
            if addon_manager is not None:
                self.addonManager = addon_manager

    fake_mw = FakeMw()

    for profile_name in profiles:
        if profile_name == current_profile:
            continue
        profile_path = tmp_path / "profiles" / profile_name
        profile_path.mkdir(parents=True)
        (profile_path / "collection.anki2").write_text("", encoding="utf-8")

    def open_collection(path: str) -> FakeCollection:
        collection = FakeCollection(Path(path).parent.name)
        fake_mw.opened_collections.append(collection)
        return collection

    for module in modules_with_mw:
        monkeypatch.setattr(module, "mw", fake_mw)

    for module in modules_with_collection:
        monkeypatch.setattr(module, "Collection", open_collection)

    return fake_mw
