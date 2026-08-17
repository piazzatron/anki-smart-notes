import { describe, expect, test } from "bun:test"

import type { AppState, SmartField } from "@/types/api"

import { groupSmartFields } from "./groupSmartFields"

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
  appVersion: "test",
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
  account: { status: "UNAUTHENTICATED", plan: null, email: null },
  featureFlags: { reviewFreeMonth: false },
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
  settings: {
    generateAtReview: false,
    regenerateWhenBatching: false,
    debug: false,
    legacyOpenAiEnabled: false,
    legacyOpenAiKey: null,
    legacyOpenAiModel: "gpt-5-mini",
    legacyOpenAiHost: null,
    showWizardCompletion: true,
    didDismissReviewPrompt: false,
    didDismissDiscordPrompt: false,
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
})
