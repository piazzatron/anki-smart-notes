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

import type { AccountState, SelectedNote } from "@/types/api"

import type { PromptTesterControls } from "./usePromptTester"

Object.defineProperty(globalThis, "window", {
  value: { location: { search: "" } },
})

const { getPromptTestCardState, getSaveTestResultTarget } =
  await import("./promptTestCard")

const ACCOUNT: AccountState = {
  plan: {
    planId: "medium1",
    planType: "medium",
    planName: "Standard",
    notesUsed: null,
    notesLimit: null,
    daysLeft: 20,
    textCreditsUsed: 0,
    textCreditsCapacity: 100,
    voiceCreditsUsed: 0,
    voiceCreditsCapacity: 100,
    imageCreditsUsed: 0,
    imageCreditsCapacity: 100,
    totalCreditsUsed: 0,
    totalCreditsCapacity: 300,
  },
  subscription: "PAID_PLAN_ACTIVE",
  email: "person@example.com",
}
const DECKS = [{ id: 1, name: "Japanese" }]
const NOTE_TYPES = [
  { fields: ["Front", "Back"], id: 10, name: "Basic" },
  { fields: ["Expression"], id: 20, name: "Japanese" },
]
const NOTE: SelectedNote = {
  cardId: 42,
  deckId: 1,
  fields: { Back: "manger", Front: "eat" },
  id: 7,
  noteTypeId: 10,
}

const testerControls = (
  overrides: Partial<PromptTesterControls<unknown>> = {},
): PromptTesterControls<unknown> => ({
  canRunWithoutCard: false,
  dismissError: () => undefined,
  error: null,
  hasNoteTypeMismatch: false,
  isPromptEditable: false,
  isTesting: false,
  prompt: "Translate {{Front}}",
  requiredNoteTypeId: 10,
  result: null,
  runTest: async () => undefined,
  selectedNote: NOTE,
  selection: { note: NOTE },
  setError: () => undefined,
  setPrompt: () => undefined,
  ...overrides,
})

const cardState = (
  overrides: Partial<PromptTesterControls<unknown>> = {},
  account: AccountState | null = ACCOUNT,
) =>
  getPromptTestCardState({
    account,
    decks: DECKS,
    noteTypes: NOTE_TYPES,
    tester: testerControls(overrides),
  })

describe("getPromptTestCardState", () => {
  test("names the selected card and allows the run", () => {
    const state = cardState()

    expect(state.deckName).toBe("Japanese")
    expect(state.noteTypeName).toBe("Basic")
    expect(state.requiredNoteTypeName).toBe("Basic")
    expect([...state.referencedFieldNames]).toEqual(["Front"])
    expect(state.missingFieldNames).toEqual([])
    expect(state.runDisabled).toBe(false)
  })

  test("blocks the run when the prompt references fields the card lacks", () => {
    const state = cardState({ prompt: "Translate {{Front}} and {{Reading}}" })

    expect(state.missingFieldNames).toEqual(["Reading"])
    expect(state.runDisabled).toBe(true)
  })

  test("blocks the run on no card, a note-type mismatch, an empty prompt, a run in flight, or no generation access", () => {
    expect(cardState({ selectedNote: null }).runDisabled).toBe(true)
    expect(cardState({ hasNoteTypeMismatch: true }).runDisabled).toBe(true)
    expect(cardState({ prompt: "   " }).runDisabled).toBe(true)
    expect(cardState({ isTesting: true }).runDisabled).toBe(true)
    expect(
      cardState({}, { ...ACCOUNT, subscription: "FREE_TRIAL_EXPIRED" })
        .runDisabled,
    ).toBe(true)
    expect(cardState({}, null).runDisabled).toBe(true)
  })

  test("allows literal text but not field references without a selected card", () => {
    expect(
      cardState({
        canRunWithoutCard: true,
        prompt: "This is a voice test.",
        selectedNote: null,
      }).runDisabled,
    ).toBe(false)
    expect(
      cardState({
        canRunWithoutCard: true,
        prompt: "Speak {{Front}}",
        selectedNote: null,
      }).runDisabled,
    ).toBe(true)
  })
})

describe("saving a test result to the card", () => {
  test("addresses the card the test ran against and the field being authored", () => {
    expect(
      getSaveTestResultTarget({
        fieldName: "Back",
        selectedNote: NOTE,
        token: "token-1",
      }),
    ).toEqual({
      cardId: 42,
      fieldName: "Back",
      token: "token-1",
    })
  })

  test("offers nothing when the tested card lacks the authored field", () => {
    expect(
      getSaveTestResultTarget({
        fieldName: "Meaning",
        selectedNote: NOTE,
        token: "token-1",
      }),
    ).toBeNull()
  })
})
