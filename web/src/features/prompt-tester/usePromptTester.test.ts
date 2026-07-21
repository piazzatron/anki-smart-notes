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

import { describe, expect, test } from "bun:test"

Object.defineProperty(globalThis, "window", {
  value: { location: { search: "" } },
})

const { getVisiblePromptTestResult } = await import("./usePromptTester")

const result = {
  cardId: 42,
  latencyMs: 125,
  model: "gpt-5-mini",
  text: "Generated text",
}

describe("usePromptTester", () => {
  test("only exposes a result for the currently selected card", () => {
    expect(getVisiblePromptTestResult(result, 42)).toBe(result)
    expect(getVisiblePromptTestResult(result, 7)).toBeNull()
    expect(getVisiblePromptTestResult(result, null)).toBeNull()
  })
})
