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

import { resolvePromptReferences } from "./resolvePromptReferences"

describe("resolvePromptReferences", () => {
  test("resolves repeated mixed-case references while preserving literal text and field names", () => {
    const result = resolvePromptReferences(
      "Define {{front}}: {{FRONT}} / {{bAcK}}.",
      {
        Back: "eat",
        Front: "食べる",
      },
    )

    expect(result.parts.map((part) => part.text).join("")).toBe(
      "Define 食べる: 食べる / eat.",
    )
    expect(
      result.parts.filter((part) => part.isReference).map((part) => part.text),
    ).toEqual(["食べる", "食べる", "eat"])
    expect(result.referencedFields).toEqual([
      ["Back", "eat"],
      ["Front", "食べる"],
    ])
    expect(result.missingFieldNames).toEqual([])
    expect(result.hasFieldReferences).toBe(true)
  })

  test("distinguishes empty values from missing fields and preserves unresolved references", () => {
    const result = resolvePromptReferences(
      "{{front}} / {{Missing}} / {{Missing}}",
      { Front: "" },
    )

    expect(result.parts.map((part) => part.text).join("")).toBe(
      " / {{Missing}} / {{Missing}}",
    )
    expect(result.missingFieldNames).toEqual(["Missing"])
    expect(result.referencedFields).toEqual([["Front", ""]])
  })

  test("handles literal and cardless prompts", () => {
    const literal = resolvePromptReferences("Explain this.", {})
    expect(literal.parts).toEqual([
      { text: "Explain this.", isReference: false },
    ])
    expect(literal.hasFieldReferences).toBe(false)
    expect(resolvePromptReferences("", {}).parts).toEqual([])

    const cardless = resolvePromptReferences("{{Front}}", {})
    expect(cardless.hasFieldReferences).toBe(true)
    expect(cardless.missingFieldNames).toEqual(["Front"])
    expect(cardless.parts).toEqual([{ text: "{{Front}}", isReference: true }])
  })
})
