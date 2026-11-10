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

import { chatSettingsMatch } from "@/features/text-generation/intelligence"
import type { AppState, SmartField } from "@/types/api"

import {
  buildSmartFieldPayload,
  createFieldEditorDraft,
  getFirstAvailableField,
  hasSmartFieldCollision,
  needsPromptWrite,
  promptModePreferenceAfterSave,
  pinUnlessDefault,
  resetPromptOnRetarget,
  validateFieldEditorDraft,
} from "./fieldEditor"

const defaults: AppState["defaults"] = {
  chat: {
    provider: "auto",
    model: "auto",
    reasoningLevel: "off",
    webSearchEnabled: false,
    stripHtml: true,
  },
  image: { provider: "openai", model: "gpt-image-1.5-low", stripHtml: true },
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
    stripHtml: true,
  },
}

const appState = {
  noteTypes: [{ id: 10, name: "Basic", fields: ["Front", "Meaning", "Audio"] }],
  smartFields: [existingField],
  globalDeckId: 1,
  settings: { prefersWritingPrompts: false },
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
    expect(validateFieldEditorDraft(chatDraft, [], 1)).toBe("Write a prompt")

    chatDraft.target.fieldType = "image"
    expect(validateFieldEditorDraft(chatDraft, [], 1)).toBe("Write a prompt")

    chatDraft.target.fieldType = "tts"
    chatDraft.sourceFieldName = ""
    expect(validateFieldEditorDraft(chatDraft, [], 1)).toBe(
      "Choose a source field",
    )
  })

  test("rejects inputs filled by voice or image Smart Fields", () => {
    const audioField: SmartField = {
      id: "audio",
      noteTypeId: 10,
      deckId: 1,
      targetFieldName: "Audio",
      fieldType: "tts",
      enabled: true,
      settings: {
        sourceFieldName: "Front",
        ...defaults.tts,
        usesDefaultGenerationSettings: true,
      },
    }
    const draft = createFieldEditorDraft(appState, {
      field: existingField,
      mode: "edit",
    })

    draft.prompt = "Define {{audio}}"
    expect(validateFieldEditorDraft(draft, [audioField], 1)).toContain("Audio")

    draft.target.fieldType = "tts"
    draft.sourceFieldName = "Audio"
    expect(validateFieldEditorDraft(draft, [audioField], 1)).toContain("Audio")

    draft.sourceFieldName = "Front"
    expect(validateFieldEditorDraft(draft, [audioField], 1)).toBeNull()
  })

  test("lets a retargeted voice field read its former target", () => {
    const audioField: SmartField = {
      id: "audio",
      noteTypeId: 10,
      deckId: 1,
      targetFieldName: "Audio",
      fieldType: "tts",
      enabled: true,
      settings: {
        sourceFieldName: "Front",
        ...defaults.tts,
        usesDefaultGenerationSettings: true,
      },
    }
    const draft = createFieldEditorDraft(
      { ...appState, smartFields: [audioField] },
      { field: audioField, mode: "edit" },
    )
    draft.target.targetFieldName = "Meaning"
    draft.sourceFieldName = "Audio"

    expect(validateFieldEditorDraft(draft, [audioField], 1)).toBeNull()
  })

  test("requires duplicate fields to be retargeted", () => {
    const draft = createFieldEditorDraft(appState, {
      field: existingField,
      mode: "duplicate",
    })

    expect(validateFieldEditorDraft(draft, [existingField], 1)).toContain(
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
        stripHtml: true,
      },
    })
  })

  test("keeps a custom field's HTML stripping choice through an edit", () => {
    const field: SmartField = {
      ...existingField,
      settings: {
        ...existingField.settings,
        stripHtml: false,
        usesDefaultGenerationSettings: false,
      },
    }
    const draft = createFieldEditorDraft(appState, { field, mode: "edit" })

    expect(buildSmartFieldPayload(draft, defaults, field).settings).toEqual(
      expect.objectContaining({ stripHtml: false }),
    )
  })

  test("an edit back to the default's values follows the default again", () => {
    expect(pinUnlessDefault({ ...defaults.chat }, defaults.chat)).toBeNull()

    const highIntelligence = { ...defaults.chat, reasoningLevel: "high" }
    expect(pinUnlessDefault(highIntelligence, defaults.chat)).toBe(
      highIntelligence,
    )
  })

  test("chat settings match the default by what the picker shows", () => {
    // Older Auto defaults store Standard as "low"; the slider writes "off".
    const olderDefault = { ...defaults.chat, reasoningLevel: "low" }
    const standard = { ...defaults.chat, reasoningLevel: "off" }
    expect(
      pinUnlessDefault(standard, olderDefault, chatSettingsMatch),
    ).toBeNull()

    const high = { ...defaults.chat, reasoningLevel: "high" }
    expect(pinUnlessDefault(high, olderDefault, chatSettingsMatch)).toBe(high)
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
      model: "z-image-turbo",
      stripHtml: false,
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
        model: "z-image-turbo",
        usesDefaultGenerationSettings: false,
        stripHtml: false,
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
    expect(validateFieldEditorDraft(draft, [existingField], 1)).toBeNull()
  })
})

// Test and Save write the prompt first exactly when this says so, and Save is enabled on
// it, so a wrong answer either saves a stale prompt or bills an extra write.
describe("needsPromptWrite", () => {
  test.each([
    ["describe", "Translate it", null, true],
    ["describe", "Translate it", "Translate it", false],
    ["describe", "Translate it again", "Translate it", true],
    ["describe", "   ", null, false],
    ["write", "Translate it", null, false],
  ] as const)(
    "%s mode, description %p written from %p: %p",
    (promptMode, writePrompt, generatedFrom, expected) => {
      const draft = {
        ...createFieldEditorDraft(appState, { mode: "create" }),
        generatedFrom,
        promptMode,
        writePrompt,
      }
      expect(needsPromptWrite(draft)).toBe(expected)
    },
  )

  test("never for a voice field, which has no prompt", () => {
    const draft = createFieldEditorDraft(appState, { mode: "create" })
    expect(
      needsPromptWrite({
        ...draft,
        target: { ...draft.target, fieldType: "tts" },
        writePrompt: "Read it",
      }),
    ).toBe(false)
  })
})

describe("resetPromptOnRetarget", () => {
  const described = {
    ...createFieldEditorDraft(appState, { mode: "create" }),
    generatedFrom: "Translate Front",
    prompt: "Translate {{Front}}.",
    promptMode: "write" as const,
    writePrompt: "Translate Front",
  }
  const otherField = {
    ...described,
    target: { ...described.target, targetFieldName: "Audio" },
  }

  test("a new field starts its description and prompt over", () => {
    expect(
      resetPromptOnRetarget({
        current: described,
        mode: "create",
        next: otherField,
        prefersWritingPrompts: false,
      }),
    ).toEqual({
      ...otherField,
      generatedFrom: null,
      prompt: "",
      promptMode: "describe",
      writePrompt: "",
    })
  })

  test("editing keeps the field's own prompt", () => {
    const next = resetPromptOnRetarget({
      current: described,
      mode: "edit",
      next: otherField,
      prefersWritingPrompts: false,
    })
    expect(next.prompt).toBe("Translate {{Front}}.")
    expect(next.promptMode).toBe("write")
    expect(next.writePrompt).toBe("")
  })

  test("leaves the draft alone when the target didn't change", () => {
    expect(
      resetPromptOnRetarget({
        current: described,
        mode: "create",
        next: described,
        prefersWritingPrompts: false,
      }),
    ).toBe(described)
  })

  test("a new field starts in the mode the user last saved with", () => {
    expect(
      resetPromptOnRetarget({
        current: described,
        mode: "create",
        next: otherField,
        prefersWritingPrompts: true,
      }).promptMode,
    ).toBe("write")
  })
})

describe("promptModePreferenceAfterSave", () => {
  const draft = createFieldEditorDraft(appState, { mode: "create" })

  test.each([
    ["create", "write", false, true],
    ["create", "describe", true, false],
    ["create", "write", true, null],
    ["edit", "write", false, null],
    ["duplicate", "write", false, null],
  ] as const)(
    "%s saved in %s mode, preferring write %p: %p",
    (mode, promptMode, prefersWritingPrompts, expected) => {
      expect(
        promptModePreferenceAfterSave({
          draft: { ...draft, promptMode },
          mode,
          prefersWritingPrompts,
        }),
      ).toBe(expected)
    },
  )
})

describe("a new field's prompt mode", () => {
  test.each([
    [false, "describe"],
    [true, "write"],
  ] as const)(
    "with prefersWritingPrompts %p, opens in %p",
    (prefersWritingPrompts, expected) => {
      const state = {
        ...appState,
        settings: { ...appState.settings, prefersWritingPrompts },
      }
      expect(createFieldEditorDraft(state, { mode: "create" }).promptMode).toBe(
        expected,
      )
    },
  )
})
