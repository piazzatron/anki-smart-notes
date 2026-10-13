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
  getRandomTestCardArgs,
  selectPromptTestRuns,
} = await import("./usePromptTester")

// Newest first, as the tester stores them.
const runs = [
  { cardId: 42, id: 3 },
  { cardId: 7, id: 2 },
  { cardId: 42, id: 1 },
]

describe("usePromptTester", () => {
  test("only exposes results for the currently selected card", () => {
    const forCard = selectPromptTestRuns({
      runs,
      selectedCardId: 42,
      viewedRunId: null,
    })
    expect(forCard.history.map((run) => run.id)).toEqual([3, 1])
    expect(forCard.run?.id).toBe(3)

    expect(
      selectPromptTestRuns({ runs, selectedCardId: null, viewedRunId: null })
        .run,
    ).toBeNull()
  })

  test("shows an earlier run on request, but only the newest run overall can be saved", () => {
    const earlier = selectPromptTestRuns({
      runs,
      selectedCardId: 42,
      viewedRunId: 1,
    })
    expect(earlier.run?.id).toBe(1)
    expect(earlier.isNewestRun).toBe(false)

    expect(
      selectPromptTestRuns({ runs, selectedCardId: 42, viewedRunId: 3 })
        .isNewestRun,
    ).toBe(true)
    // Card 7's run is newest for that card but not overall: another test ran since.
    expect(
      selectPromptTestRuns({ runs, selectedCardId: 7, viewedRunId: null })
        .isNewestRun,
    ).toBe(false)
  })

  test("falls back to the newest run when the viewed one belongs to another card", () => {
    expect(
      selectPromptTestRuns({ runs, selectedCardId: 42, viewedRunId: 2 }).run
        ?.id,
    ).toBe(3)
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

  test("starts a field tester on a random card only when no usable card is picked", () => {
    const noteTypes = [{ fields: ["Front", "Back"], id: 20, name: "Basic" }]
    const picked = {
      note: {
        cardId: 42,
        deckId: 1,
        fields: { Front: "Bonjour" },
        id: 7,
        noteTypeId: 20,
      },
    }
    const args = {
      deckId: 1,
      noteTypes,
      prompt: "Use {{front}} and {{Missing}}",
      requiredNoteTypeId: 20,
    }

    expect(
      getRandomTestCardArgs({
        ...args,
        initialSelection: { count: 0, note: null },
      }),
    ).toEqual({ deckId: 1, filledFieldNames: ["Front"], noteTypeId: 20 })
    expect(
      getRandomTestCardArgs({ ...args, initialSelection: picked }),
    ).toBeNull()
    // Defaults testers aren't bound to a note type, so there is nothing to draw from.
    expect(
      getRandomTestCardArgs({
        initialSelection: null,
        noteTypes,
        prompt: "Use {{Front}}",
      }),
    ).toBeNull()
  })
})
