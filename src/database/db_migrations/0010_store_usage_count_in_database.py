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

# How many times the user has generated, per profile. It lived in the add-on's config
# file, where each bump rewrote the whole file; here a bump is one statement. The
# usage service carries a profile's old count over from the config the first time
# it reads it.
steps = [
    step(
        "CREATE TABLE usage_counts ("
        "profile_name TEXT PRIMARY KEY, "
        "times_used INTEGER NOT NULL CHECK (times_used >= 0));",
        "DROP TABLE usage_counts;",
    ),
]
