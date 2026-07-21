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

import type { AppState, SmartField } from "@/types/api"

import {
  buildSmartFieldSavePayload,
  createFieldEditorDraft,
  getFirstAvailableField,
  hasSmartFieldCollision,
  validateFieldEditorDraft,
} from "./fieldEditor"

const defaults: AppState["defaults"] = {
  chat: {
    provider: "auto",
    model: "auto",
    reasoningLevel: "off",
    webSearchEnabled: false,
  },
  image: { provider: "openai", model: "gpt-image-1.5-low" },
  tts: { provider: "google", model: "standard", voiceId: "voice" },
}

const existingField: SmartField = {
  id: "meaning",
  noteTypeId: 10,
  deckId: 1,
  targetFieldName: "Meaning",
  fieldType: "chat",
  enabled: false,
  settings: {
    promptText: "Translate {{Front}}",
    ...defaults.chat,
    usesDefaultGenerationSettings: true,
  },
}

const appState = {
  noteTypes: [{ id: 10, name: "Basic", fields: ["Front", "Meaning", "Audio"] }],
  smartFields: [existingField],
  globalDeckId: 1,
} as AppState

describe("field editor helpers", () => {
  test("detects exact target collisions", () => {
    expect(
      hasSmartFieldCollision([existingField], {
        deckId: 1,
        noteTypeId: 10,
        targetFieldName: "Meaning",
      }),
    ).toBe(true)
    expect(
      hasSmartFieldCollision([existingField], {
        deckId: 1,
        noteTypeId: 10,
        targetFieldName: "meaning",
      }),
    ).toBe(false)
    expect(
      getFirstAvailableField(appState.noteTypes[0], [existingField], 1),
    ).toBe("Front")
  })

  test("validates prompts and TTS source fields", () => {
    const chatDraft = createFieldEditorDraft(appState, "create")
    expect(validateFieldEditorDraft(chatDraft, [])).toBe("Write a prompt")

    chatDraft.target.fieldType = "image"
    expect(validateFieldEditorDraft(chatDraft, [])).toBe("Write a prompt")

    chatDraft.target.fieldType = "tts"
    chatDraft.sourceFieldName = ""
    expect(validateFieldEditorDraft(chatDraft, [])).toBe(
      "Choose a source field",
    )
  })

  test("requires duplicate fields to be retargeted", () => {
    const draft = createFieldEditorDraft(appState, "duplicate", existingField)

    expect(validateFieldEditorDraft(draft, [existingField])).toContain(
      "already has a Smart Field",
    )
  })

  test("snapshots current defaults when following defaults", () => {
    const draft = createFieldEditorDraft(appState, "create")
    draft.prompt = "Explain {{Front}}"

    expect(buildSmartFieldSavePayload(draft, defaults)).toEqual({
      noteTypeId: 10,
      deckId: 1,
      targetFieldName: "Front",
      fieldType: "chat",
      enabled: true,
      settings: {
        promptText: "Explain {{Front}}",
        ...defaults.chat,
        usesDefaultGenerationSettings: true,
      },
    })
  })

  test("uses pinned image settings and enables a duplicate", () => {
    const draft = createFieldEditorDraft(appState, "duplicate", existingField)
    draft.target = {
      deckId: 1,
      fieldType: "image",
      noteTypeId: 10,
      targetFieldName: "Audio",
    }
    draft.prompt = "Picture {{Front}}"
    draft.pinnedSettings.image = {
      provider: "replicate",
      model: "flux-dev",
    }

    expect(buildSmartFieldSavePayload(draft, defaults, existingField)).toEqual({
      noteTypeId: 10,
      deckId: 1,
      targetFieldName: "Audio",
      fieldType: "image",
      enabled: true,
      settings: {
        promptText: "Picture {{Front}}",
        provider: "replicate",
        model: "flux-dev",
        usesDefaultGenerationSettings: false,
      },
    })
  })

  test("builds a complete TTS payload from current defaults", () => {
    const draft = createFieldEditorDraft(appState, "create")
    draft.target.fieldType = "tts"
    draft.sourceFieldName = "Meaning"

    expect(buildSmartFieldSavePayload(draft, defaults)).toEqual({
      noteTypeId: 10,
      deckId: 1,
      targetFieldName: "Front",
      fieldType: "tts",
      enabled: true,
      settings: {
        sourceFieldName: "Meaning",
        ...defaults.tts,
        usesDefaultGenerationSettings: true,
      },
    })
  })

  test("preserves enabled state when editing", () => {
    const draft = createFieldEditorDraft(appState, "edit", existingField)

    expect(draft.step).toBe(2)
    expect(
      buildSmartFieldSavePayload(draft, defaults, existingField).enabled,
    ).toBe(false)
  })
})
