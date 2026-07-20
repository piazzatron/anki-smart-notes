import { describe, expect, test } from "bun:test"

import type { AppState } from "@/store/appStore"

import { groupSmartFields } from "./groupSmartFields"
import type { SmartField } from "./types"

const field = (id: string, noteTypeId: number, deckId: number): SmartField => ({
  id,
  noteTypeId,
  deckId,
  targetFieldName: id,
  fieldType: "chat",
  enabled: true,
  settings: {
    promptText: id,
    provider: "auto",
    model: "auto",
    reasoningLevel: "off",
    webSearchEnabled: false,
    usesDefaultGenerationSettings: true,
  },
})

const stateWith = (smartFields: SmartField[]): AppState => ({
  schemaVersion: 1,
  smartFields,
  noteTypes: [
    { id: 10, name: "Japanese", fields: ["Reading"] },
    { id: 20, name: "Basic", fields: ["Back"] },
  ],
  decks: [
    { id: 1, name: "All Decks" },
    { id: 2, name: "JLPT N5" },
  ],
  globalDeckId: 1,
  account: { subscription: "UNAUTHENTICATED", plan: null },
  defaults: {
    chat: {
      provider: "auto",
      model: "auto",
      reasoningLevel: "off",
      webSearchEnabled: false,
    },
    tts: { provider: "google", model: "standard", voiceId: "voice" },
    image: { provider: "openai", model: "gpt-image-1.5-low" },
  },
})

describe("groupSmartFields", () => {
  test("puts global fields first and groups note types within each deck", () => {
    const groups = groupSmartFields(
      stateWith([
        field("deck-field", 10, 2),
        field("basic", 20, 1),
        field("jp", 10, 1),
      ]),
    )

    expect(groups.map((group) => group.deck.name)).toEqual([
      "All Decks",
      "JLPT N5",
    ])
    expect(groups[0]?.noteTypes.map((group) => group.noteType.name)).toEqual([
      "Japanese",
      "Basic",
    ])
  })

  test("fails fast when a field references a missing deck", () => {
    expect(() =>
      groupSmartFields(stateWith([field("broken", 10, 999)])),
    ).toThrow("references missing deck 999")
  })
})
