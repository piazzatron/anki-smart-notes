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
  buildSmartFieldPayload,
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
    const chatDraft = createFieldEditorDraft(appState, { mode: "create" })
    expect(chatDraft.validPromptFieldsRevealed).toBe(false)
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
    const draft = createFieldEditorDraft(appState, {
      field: existingField,
      mode: "duplicate",
    })

    expect(validateFieldEditorDraft(draft, [existingField])).toContain(
      "already has a Smart Field",
    )
  })

  test("snapshots current defaults when following defaults", () => {
    const draft = createFieldEditorDraft(appState, { mode: "create" })
    draft.prompt = "Explain {{Front}}"

    expect(buildSmartFieldPayload(draft, defaults)).toEqual({
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

  test("starts a new field on the requested existing note type", () => {
    const requestedNoteTypeField: SmartField = {
      ...existingField,
      id: "expression",
      noteTypeId: 20,
      targetFieldName: "Expression",
    }
    const state = {
      ...appState,
      noteTypes: [
        ...appState.noteTypes,
        {
          fields: ["Expression", "Meaning", "Audio"],
          id: 20,
          name: "Japanese",
        },
      ],
      smartFields: [existingField, requestedNoteTypeField],
    }

    const draft = createFieldEditorDraft(state, {
      initialNoteTypeId: 20,
      mode: "create",
    })

    expect(draft.target.noteTypeId).toBe(20)
    expect(draft.target.targetFieldName).toBe("Meaning")
    expect(draft.sourceFieldName).toBe("Expression")
  })

  test("uses pinned image settings and enables a duplicate", () => {
    const draft = createFieldEditorDraft(appState, {
      field: existingField,
      mode: "duplicate",
    })
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

    expect(buildSmartFieldPayload(draft, defaults, existingField)).toEqual({
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
    const draft = createFieldEditorDraft(appState, { mode: "create" })
    draft.target.fieldType = "tts"
    draft.sourceFieldName = "Meaning"

    expect(buildSmartFieldPayload(draft, defaults)).toEqual({
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
    const draft = createFieldEditorDraft(appState, {
      field: existingField,
      mode: "edit",
    })

    expect(buildSmartFieldPayload(draft, defaults, existingField).enabled).toBe(
      false,
    )
  })

  test("editing opens on step 1 and does not collide with its own binding", () => {
    const draft = createFieldEditorDraft(appState, {
      field: existingField,
      mode: "edit",
    })

    expect(draft.step).toBe(1)
    expect(draft.editingFieldId).toBe(existingField.id)
    expect(validateFieldEditorDraft(draft, [existingField])).toBeNull()
  })
})
