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

import { expect, test } from "bun:test"

import { htmlToText } from "./htmlToText"

// The same cases as test_interpolate_prompt_strips_field_html, which pins the
// plugin's html_to_text: the preview has to match what generation sends.
test.each([
  [
    '<div class="yomitan-glossary"><span><style>.x { color: red }</style>' +
      '<img src="v5g.svg"></span><div><ul><li>to hurry</li><li>to rush</li></ul>' +
      "</div></div>",
    "to hurry\nto rush",
  ],
  ["Tom&nbsp;&amp; Jerry<br>cat &lt;3 &#x41;&#66;", "Tom & Jerry\ncat <3 AB"],
  ['<img src="dog.jpg">', ""],
  ["a&#x110000;b", "a\ufffdb"],
])("htmlToText(%p)", (html, text) => {
  expect(htmlToText(html)).toBe(text)
})
