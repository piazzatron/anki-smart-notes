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

# Set the test environment flag FIRST, before any other imports
import os

os.environ["IS_TEST"] = "True"

import sys
from pathlib import Path

# Add the parent directory to Python path so we can import src modules directly
parent_dir = Path(__file__).parent.parent
sys.path.insert(0, str(parent_dir))

# CRITICAL: Import anki.collection first to break the circular import
import anki.collection

# hack: to fix unused import error
_ = anki.collection.Collection
