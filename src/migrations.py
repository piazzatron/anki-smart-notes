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

from .database import apply_database_bootstrap_migrations, apply_database_migrations
from .smart_field_migration import (
    migrate_legacy_chat_config_to_auto,
    migrate_legacy_smart_field_config,
)


def run_migrations() -> None:
    # Legacy config import writes into SQLite, so the table schema must exist
    # first. Run all data migrations afterward so imported rows are included.
    apply_database_bootstrap_migrations()
    migrate_legacy_smart_field_config()
    apply_database_migrations()
    migrate_legacy_chat_config_to_auto()
