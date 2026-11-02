/*
 * Copyright (C) 2024 Michael Piazza
 *
 * This file is part of Smart Notes.
 *
 * Smart Notes is free software: you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation, either version 3 of the License, or
 * (at your option) any later version.
 *
 * Smart Notes is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with Smart Notes. If not, see <https://www.gnu.org/licenses/>.
 */

const HIDDEN_CONTENT = /<(style|script)\b[\s\S]*?<\/\1\s*>|<!--[\s\S]*?-->/gi
const LINE_BREAK = /<\/?(?:br|div|p|li|ul|ol|tr|h[1-6])\b[^>]*>/gi
const TAG = /<[^>]*>/g
const ENTITY = /&(#x[\da-f]+|#\d+|[a-z]+);/gi
const NAMED_ENTITIES: Record<string, string> = {
  amp: "&",
  apos: "'",
  gt: ">",
  lt: "<",
  // Anki's editor writes &nbsp; for ordinary spaces.
  nbsp: " ",
  quot: '"',
}

/** Field HTML as plain text, the way `html_to_text` in the plugin's
 *  `prompt_helpers.py` puts it into a prompt, so the tester shows what was sent. Only
 *  the common named entities are decoded; rarer ones stay as written in the preview. */
export const htmlToText = (html: string): string =>
  html
    .replace(HIDDEN_CONTENT, "")
    .replace(LINE_BREAK, "\n")
    .replace(TAG, "")
    .replace(ENTITY, (entity, name: string) => {
      if (!name.startsWith("#")) return NAMED_ENTITIES[name] ?? entity
      const isHex = name[1] === "x" || name[1] === "X"
      const code = parseInt(name.slice(isHex ? 2 : 1), isHex ? 16 : 10)
      // Past Unicode's range, fromCodePoint throws; Python's unescape gives U+FFFD.
      return code > 0x10ffff ? "\ufffd" : String.fromCodePoint(code)
    })
    .split("\n")
    .map((line) => line.trim())
    .filter((line) => line !== "")
    .join("\n")
