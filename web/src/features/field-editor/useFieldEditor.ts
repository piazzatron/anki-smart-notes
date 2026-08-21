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

import { useState } from "react"

import { errorMessage } from "@/lib/errors"
import { trackSmartFieldSaved } from "@/services/analytics"
import {
  createSmartField,
  generatePrompt,
  saveSettings,
  updateSmartField,
} from "@/services/commands"
import type {
  AppState,
  ChatGenerationSettings,
  ImageGenerationSettings,
  SmartField,
  TTSGenerationSettings,
} from "@/types/api"

import {
  buildSmartFieldPayload,
  createFieldEditorDraft,
  getFirstAvailableField,
  getFirstSourceField,
  validateFieldEditorDraft,
} from "./fieldEditor"
import type {
  FieldEditorDraft,
  FieldEditorMode,
  FieldEditorStep,
  FieldTargetDraft,
} from "./fieldEditor"

interface UseFieldEditorArgs {
  field?: SmartField
  initialNoteTypeId?: number
  initialStep?: FieldEditorStep
  mode: FieldEditorMode
  onClose: () => void
  state: AppState
}

export interface FieldEditorControls {
  dismissError: () => void
  form: FieldEditorDraft
  generateDraftPrompt: () => Promise<void>
  save: () => Promise<void>
  setPinnedChat: (settings: ChatGenerationSettings | null) => void
  setPinnedImage: (settings: ImageGenerationSettings | null) => void
  setPinnedTTS: (settings: TTSGenerationSettings | null) => void
  setStep: (step: FieldEditorStep) => void
  setTarget: (updates: Partial<FieldTargetDraft>) => void
  setWizardCompletionHidden: () => Promise<void>
  update: (updates: Partial<FieldEditorDraft>) => void
}

export const useFieldEditor = ({
  field,
  initialNoteTypeId,
  initialStep,
  mode,
  onClose,
  state,
}: UseFieldEditorArgs): FieldEditorControls => {
  const [form, setForm] = useState(() =>
    createFieldEditorDraft(state, {
      field,
      initialNoteTypeId,
      initialStep,
      mode,
    }),
  )
  const update = (updates: Partial<FieldEditorDraft>) =>
    setForm((current) => ({ ...current, ...updates }))
  const setPinned = (
    key: keyof FieldEditorDraft["pinnedSettings"],
    settings:
      | ChatGenerationSettings
      | ImageGenerationSettings
      | TTSGenerationSettings
      | null,
  ) =>
    setForm((current) => ({
      ...current,
      pinnedSettings: { ...current.pinnedSettings, [key]: settings },
    }))

  const changeTarget = (updates: Partial<FieldTargetDraft>) => {
    setForm((current) => {
      const nextTarget = { ...current.target, ...updates }
      if (updates.noteTypeId === undefined) {
        return { ...current, error: null, target: nextTarget }
      }

      const noteType = state.noteTypes.find(
        (item) => item.id === updates.noteTypeId,
      )
      nextTarget.targetFieldName = getFirstAvailableField(
        noteType,
        state.smartFields,
        nextTarget.deckId,
      )
      return {
        ...current,
        error: null,
        sourceFieldName: getFirstSourceField(
          noteType,
          nextTarget.targetFieldName,
        ),
        target: nextTarget,
      }
    })
  }

  const generateDraftPrompt = async () => {
    if (form.target.fieldType === "tts" || form.writePrompt.trim() === "") {
      return
    }

    update({ error: null, isGenerating: true })
    try {
      const result = await generatePrompt({
        noteTypeId: form.target.noteTypeId,
        deckId: form.target.deckId,
        targetFieldName: form.target.targetFieldName,
        fieldType: form.target.fieldType,
        generationPrompt: form.writePrompt,
      })
      update({ prompt: result.prompt })
    } catch (error) {
      update({
        error: errorMessage(error, "Could not write the prompt"),
      })
    } finally {
      update({ isGenerating: false })
    }
  }

  const save = async () => {
    const validationError = validateFieldEditorDraft(form, state.smartFields)
    if (validationError !== null) {
      update({ error: validationError })
      return
    }

    update({ error: null, isSaving: true })
    try {
      const payload = buildSmartFieldPayload(form, state.defaults, field)
      if (mode === "edit") {
        if (field === undefined) {
          throw new Error("Cannot update a Smart Field without its id")
        }
        await updateSmartField({ ...payload, id: field.id })
      } else {
        await createSmartField(payload)
        if (mode === "create") {
          void trackSmartFieldSaved({
            appVersion: state.appVersion,
            authToken: state.account.authToken,
            fieldType: form.target.fieldType,
          }).catch(() => undefined)
        }
      }
      if (mode === "edit" || !state.settings.showWizardCompletion) {
        onClose()
        return
      }
      update({ isSaving: false, step: 3 })
    } catch (error) {
      update({
        error: errorMessage(error, "Could not save Smart Field"),
        isSaving: false,
      })
    }
  }

  const setWizardCompletionHidden = async () => {
    try {
      await saveSettings({ ...state.settings, showWizardCompletion: false })
    } catch (error) {
      update({
        error: errorMessage(error, "Could not update wizard settings"),
      })
    }
  }

  return {
    dismissError: () => update({ error: null }),
    form,
    generateDraftPrompt,
    save,
    setPinnedChat: (settings) => setPinned("chat", settings),
    setPinnedImage: (settings) => setPinned("image", settings),
    setPinnedTTS: (settings) => setPinned("tts", settings),
    setStep: (step) => update({ step }),
    setTarget: changeTarget,
    setWizardCompletionHidden,
    update,
  }
}
