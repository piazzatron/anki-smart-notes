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

import re


def convert_markdown_to_html(markdown: str) -> str:
    # Convert bold text (e.g., **bold** or __bold__)
    markdown = re.sub(r"\*\*(.*?)\*\*", r"<strong>\1</strong>", markdown)
    markdown = re.sub(r"__(.*?)__", r"<strong>\1</strong>", markdown)

    # Convert italic text (e.g., *italic* or _italic_)
    markdown = re.sub(r"\*(.*?)\*", r"<em>\1</em>", markdown)
    markdown = re.sub(r"_(.*?)_", r"<em>\1</em>", markdown)

    # Convert text sizes (e.g., # Header 1, ## Header 2, ### Header 3)
    markdown = re.sub(r"###### (.*?)\n", r"<h6>\1</h6>\n", markdown)
    markdown = re.sub(r"##### (.*?)\n", r"<h5>\1</h5>\n", markdown)
    markdown = re.sub(r"#### (.*?)\n", r"<h4>\1</h4>\n", markdown)
    markdown = re.sub(r"### (.*?)\n", r"<h3>\1</h3>\n", markdown)
    markdown = re.sub(r"## (.*?)\n", r"<h2>\1</h2>\n", markdown)
    markdown = re.sub(r"# (.*?)\n", r"<h1>\1</h1>\n", markdown)

    # Convert all head whitespace to &nbsp;
    markdown = convert_leading_whitespaces_to_html(markdown)

    # Convert newlines to <br> tags
    markdown = re.sub(r"\n", r"<br>", markdown)

    return markdown


# Convert leading whitespaces to &nbsp;
def convert_leading_whitespaces_to_html(markdown: str) -> str:
    """
    example:
      "Hello  "            -> "Hello  "
      "  "                 -> "&nbsp;&nbsp;"    <- This is a space
      "		"              -> "&nbsp;&nbsp;"    <- This is a tab
      "   Hello, World!"   -> "&nbsp;&nbsp;&nbsp;Hello, World!"
    """
    return re.sub(
        # Only match spaces and tabs, not newlines.
        r"^([ \t]+)",
        lambda match: "&nbsp;" * len(match.group(1)),
        markdown,
        flags=re.MULTILINE,
    )
