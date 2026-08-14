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
import { renderToStaticMarkup } from "react-dom/server"

import type { AppState, Catalog, PlanInfo } from "@/types/api"

import { createFieldEditorDraft } from "./fieldEditor"
import type { FieldEditorControls } from "./useFieldEditor"

if (!("window" in globalThis)) {
  Object.defineProperty(globalThis, "window", {
    configurable: true,
    value: { location: { search: "" } },
  })
}

const { StepPrompt } = await import("./StepPrompt")

const plan: PlanInfo = {
  planId: "free",
  planType: "trial",
  planName: "Free Trial",
  notesUsed: 0,
  notesLimit: 50,
  daysLeft: 5,
  textCreditsUsed: 0,
  textCreditsCapacity: 100,
  voiceCreditsUsed: 0,
  voiceCreditsCapacity: 100,
  imageCreditsUsed: 0,
  imageCreditsCapacity: 100,
  totalCreditsUsed: 0,
  totalCreditsCapacity: 300,
}

const state: AppState = {
  schemaVersion: 1,
  appVersion: "test",
  noteTypes: [
    {
      id: 10,
      name: "Japanese",
      fields: ["Expression", "Meaning", "Example"],
    },
  ],
  decks: [{ id: 1, name: "All Decks" }],
  smartFields: [],
  globalDeckId: 1,
  account: {
    subscription: "FREE_TRIAL_ACTIVE",
    plan,
    email: "person@example.com",
  },
  defaults: {
    chat: {
      provider: "auto",
      model: "auto",
      reasoningLevel: "off",
      webSearchEnabled: false,
    },
    image: { provider: "openai", model: "gpt-image-1.5-low" },
    tts: { provider: "google", model: "standard", voiceId: "test-voice" },
  },
  settings: {
    generateAtReview: true,
    regenerateWhenBatching: false,
    debug: false,
    legacyOpenAiKey: null,
    legacyOpenAiModel: "gpt-5-mini",
    legacyOpenAiHost: null,
    showWizardCompletion: true,
    didDismissDiscordPrompt: false,
  },
}

const catalog = {
  schemaVersion: 1,
  chat: {
    providers: ["auto"],
    models: [{ id: "auto", provider: "auto" }],
    reasoningLevels: ["off"],
  },
  image: { providers: [], models: [] },
} satisfies Catalog

describe("StepPrompt", () => {
  test("progressively discloses valid prompt fields", () => {
    expect(renderStep(false)).not.toContain("Valid fields:")

    const revealedMarkup = renderStep(true)
    expect(revealedMarkup).toContain("Valid fields:")
    expect(revealedMarkup).toContain("{{Expression}}")
    expect(revealedMarkup).toContain("{{Meaning}}")
  })
})

const renderStep = (validPromptFieldsRevealed: boolean): string => {
  const draft = createFieldEditorDraft(state, { mode: "create" })
  draft.target.targetFieldName = "Example"
  draft.validPromptFieldsRevealed = validPromptFieldsRevealed
  const controls = {
    form: draft,
    generateDraftPrompt: async () => undefined,
    setPinnedChat: () => undefined,
    update: () => undefined,
  } as unknown as FieldEditorControls

  return renderToStaticMarkup(
    <StepPrompt
      catalog={catalog}
      controls={controls}
      state={state}
      voiceCatalog={null}
    />,
  )
}
