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

import type {
  AppState,
  ChatGenerationSettings,
  ImageGenerationSettings,
  NoteType,
  SmartField,
  SmartFieldCreatePayload,
  TTSGenerationSettings,
} from "@/types/api"

export type FieldEditorMode = "create" | "edit" | "duplicate"
export type FieldEditorStep = 1 | 2 | 3
export type FieldType = SmartField["fieldType"]

export interface FieldTargetDraft {
  deckId: number
  fieldType: FieldType
  noteTypeId: number
  targetFieldName: string
}

export interface PinnedGenerationSettings {
  chat: ChatGenerationSettings | null
  image: ImageGenerationSettings | null
  tts: TTSGenerationSettings | null
}

export interface FieldEditorDraft {
  // The field being edited, so target collision checks can ignore its own binding.
  // Null while creating or duplicating, where every binding is somebody else's.
  editingFieldId: string | null
  error: string | null
  isGenerating: boolean
  isSaving: boolean
  mode: FieldEditorMode
  pinnedSettings: PinnedGenerationSettings
  prompt: string
  sourceFieldName: string
  step: FieldEditorStep
  target: FieldTargetDraft
  validPromptFieldsRevealed: boolean
  writePrompt: string
}

interface CreateFieldEditorDraftArgs {
  field?: SmartField
  initialNoteTypeId?: number
  initialStep?: FieldEditorStep
  mode: FieldEditorMode
}

export const createFieldEditorDraft = (
  state: AppState,
  { field, initialNoteTypeId, initialStep, mode }: CreateFieldEditorDraftArgs,
): FieldEditorDraft => {
  const noteType =
    state.noteTypes.find((item) => item.id === field?.noteTypeId) ??
    state.noteTypes.find((item) => item.id === initialNoteTypeId) ??
    state.noteTypes[0]
  const deckId = field?.deckId ?? state.globalDeckId
  const targetFieldName =
    field?.targetFieldName ??
    getFirstAvailableField(noteType, state.smartFields, deckId)
  const fieldType = field?.fieldType ?? "chat"

  return {
    editingFieldId: mode === "edit" ? (field?.id ?? null) : null,
    error: null,
    isGenerating: false,
    isSaving: false,
    mode,
    pinnedSettings: getInitialPinnedSettings(field),
    prompt:
      field?.fieldType === "chat" || field?.fieldType === "image"
        ? field.settings.promptText
        : "",
    sourceFieldName:
      field?.fieldType === "tts"
        ? field.settings.sourceFieldName
        : getFirstSourceField(noteType, targetFieldName),
    // Editing starts on step 1 too — the target is as changeable as the prompt.
    step: initialStep ?? 1,
    target: {
      deckId,
      fieldType,
      noteTypeId: noteType?.id ?? 0,
      targetFieldName,
    },
    validPromptFieldsRevealed: false,
    writePrompt: "",
  }
}

export const getFirstAvailableField = (
  noteType: NoteType | undefined,
  fields: SmartField[],
  deckId: number,
): string =>
  noteType?.fields.find(
    (fieldName) =>
      !hasSmartFieldCollision(fields, {
        deckId,
        noteTypeId: noteType.id,
        targetFieldName: fieldName,
      }),
  ) ??
  noteType?.fields[0] ??
  ""

export const getFirstSourceField = (
  noteType: NoteType | undefined,
  targetFieldName: string,
): string =>
  noteType?.fields.find((fieldName) => fieldName !== targetFieldName) ??
  noteType?.fields[0] ??
  ""

export const hasSmartFieldCollision = (
  fields: SmartField[],
  target: Pick<FieldTargetDraft, "deckId" | "noteTypeId" | "targetFieldName">,
  ignoreFieldId?: string | null,
): boolean =>
  fields.some(
    (field) =>
      field.id !== ignoreFieldId &&
      field.noteTypeId === target.noteTypeId &&
      field.deckId === target.deckId &&
      field.targetFieldName === target.targetFieldName,
  )

export const validateFieldEditorDraft = (
  draft: FieldEditorDraft,
  fields: SmartField[],
): string | null => {
  if (draft.target.noteTypeId === 0) return "Choose a note type"
  if (draft.target.targetFieldName.trim() === "") return "Choose a field"
  if (hasSmartFieldCollision(fields, draft.target, draft.editingFieldId)) {
    return `${draft.target.targetFieldName} already has a Smart Field`
  }
  if (draft.target.fieldType === "tts" && draft.sourceFieldName.trim() === "") {
    return "Choose a source field"
  }
  if (draft.target.fieldType !== "tts" && draft.prompt.trim() === "") {
    return "Write a prompt"
  }

  return null
}

export const buildSmartFieldPayload = (
  draft: FieldEditorDraft,
  defaults: AppState["defaults"],
  originalField?: SmartField,
): SmartFieldCreatePayload => {
  const base = {
    noteTypeId: draft.target.noteTypeId,
    deckId: draft.target.deckId,
    targetFieldName: draft.target.targetFieldName,
    enabled: draft.mode === "edit" ? (originalField?.enabled ?? true) : true,
  }

  if (draft.target.fieldType === "chat") {
    const settings = draft.pinnedSettings.chat ?? defaults.chat
    return {
      ...base,
      fieldType: "chat",
      settings: {
        ...settings,
        promptText: draft.prompt,
        usesDefaultGenerationSettings: draft.pinnedSettings.chat === null,
      },
    }
  }
  if (draft.target.fieldType === "image") {
    const settings = draft.pinnedSettings.image ?? defaults.image
    return {
      ...base,
      fieldType: "image",
      settings: {
        ...settings,
        promptText: draft.prompt,
        usesDefaultGenerationSettings: draft.pinnedSettings.image === null,
      },
    }
  }

  const settings = draft.pinnedSettings.tts ?? defaults.tts
  return {
    ...base,
    fieldType: "tts",
    settings: {
      ...settings,
      sourceFieldName: draft.sourceFieldName,
      usesDefaultGenerationSettings: draft.pinnedSettings.tts === null,
    },
  }
}

const getInitialPinnedSettings = (
  field: SmartField | undefined,
): PinnedGenerationSettings => {
  const pinned: PinnedGenerationSettings = {
    chat: null,
    image: null,
    tts: null,
  }
  if (field === undefined || field.settings.usesDefaultGenerationSettings) {
    return pinned
  }

  if (field.fieldType === "chat") {
    return {
      ...pinned,
      chat: {
        model: field.settings.model,
        provider: field.settings.provider,
        reasoningLevel: field.settings.reasoningLevel,
        webSearchEnabled: field.settings.webSearchEnabled,
      },
    }
  }
  if (field.fieldType === "image") {
    return {
      ...pinned,
      image: {
        model: field.settings.model,
        provider: field.settings.provider,
      },
    }
  }
  return {
    ...pinned,
    tts: {
      model: field.settings.model,
      provider: field.settings.provider,
      voiceId: field.settings.voiceId,
    },
  }
}
