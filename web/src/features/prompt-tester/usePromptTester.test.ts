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

const {
  getInitialPromptTestSelection,
  getPromptTestSelection,
  getVisiblePromptTestResult,
} = await import("./usePromptTester")

const result = {
  cardId: 42,
  latencyMs: 125,
  prompt: "Define {{Front}}",
  value: { text: "Generated text" },
}

describe("usePromptTester", () => {
  test("only exposes a result for the currently selected card", () => {
    expect(getVisiblePromptTestResult(result, 42)).toEqual({
      latencyMs: 125,
      prompt: "Define {{Front}}",
      value: { text: "Generated text" },
    })
    expect(getVisiblePromptTestResult(result, 7)).toBeNull()
    expect(getVisiblePromptTestResult(result, null)).toBeNull()
  })

  test("flags a selected card from a different required note type", () => {
    const selection = {
      note: {
        cardId: 42,
        deckId: 1,
        fields: { Front: "Bonjour" },
        id: 7,
        noteTypeId: 20,
      },
    }

    // The mismatched note stays visible — the panel shows what is picked and why it
    // cannot run.
    expect(getPromptTestSelection(selection, 10)).toEqual({
      hasNoteTypeMismatch: true,
      selectedNote: selection.note,
    })
    expect(getPromptTestSelection(selection, 20)).toEqual({
      hasNoteTypeMismatch: false,
      selectedNote: selection.note,
    })
    expect(getPromptTestSelection(selection)).toEqual({
      hasNoteTypeMismatch: false,
      selectedNote: selection.note,
    })
  })

  test("adopts an inherited selection only when it matches the required note type", () => {
    const selection = {
      note: {
        cardId: 42,
        deckId: 1,
        fields: { Front: "Bonjour" },
        id: 7,
        noteTypeId: 20,
      },
    }

    expect(
      getInitialPromptTestSelection({
        prompt: "Define {{Front}}",
        requiredNoteTypeId: 20,
        selection,
      }),
    ).toBe(selection)
    expect(
      getInitialPromptTestSelection({
        prompt: "Define {{Front}}",
        requiredNoteTypeId: 10,
        selection,
      }),
    ).toBeNull()
  })

  test("keeps inherited selections for unbound Defaults testers", () => {
    const selection = {
      note: {
        cardId: 42,
        deckId: 1,
        fields: { Front: "Bonjour" },
        id: 7,
        noteTypeId: 20,
      },
    }

    expect(
      getInitialPromptTestSelection({ prompt: "Define {{Front}}", selection }),
    ).toBe(selection)
  })

  test("drops an inherited card the prompt cannot run against", () => {
    const selection = {
      note: {
        cardId: 42,
        deckId: 1,
        fields: { Front: "Bonjour" },
        id: 7,
        noteTypeId: 20,
      },
    }

    // Nothing was picked for this tester, so it asks for a card rather than
    // complaining about one the user never chose here.
    expect(
      getInitialPromptTestSelection({
        prompt: "Translate {{Expression}}",
        selection,
      }),
    ).toBeNull()
  })
})
