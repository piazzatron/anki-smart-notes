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

import { useEffect, useState } from "react"
import { useTranslation } from "react-i18next"

import { errorMessage } from "@/lib/errors"
import { useAppStore } from "@/store/appStore"
import { trackAnalyticsEvent } from "@/services/analytics"
import {
  createSmartField,
  generatePrompt,
  saveSettings,
  suggestPrompt,
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
  // Resolves true when a prompt was written. `description` stands in for the typed one,
  // for when it was set in the same event and the form hasn't caught up.
  generateDraftPrompt: (description?: string) => Promise<boolean>
  markPromptTipSeen: () => Promise<void>
  save: () => Promise<void>
  setPinnedChat: (settings: ChatGenerationSettings | null) => void
  setPinnedImage: (settings: ImageGenerationSettings | null) => void
  setPinnedTTS: (settings: TTSGenerationSettings | null) => void
  setStep: (step: FieldEditorStep) => void
  setTarget: (updates: Partial<FieldTargetDraft>) => void
  // An AI guess at what the field is for, as an example for the describe box. Null
  // while it loads.
  suggestion: string | null
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
  const { t } = useTranslation()
  const [form, setForm] = useState(() =>
    createFieldEditorDraft(state, {
      field,
      initialNoteTypeId,
      initialStep,
      mode,
    }),
  )

  // Asked for as soon as the target is set, not when the prompt step opens, so it's
  // usually ready by the time the user gets there. Each answer is kept with the target
  // it was for, so a stale one never shows.
  const [suggested, setSuggested] = useState<{
    key: string
    suggestion: string
  } | null>(null)
  const { deckId, fieldType, noteTypeId, targetFieldName } = form.target
  const suggestionKey = `${noteTypeId}/${deckId}/${targetFieldName}/${fieldType}`
  const needsSuggestion =
    fieldType !== "tts" && suggested?.key !== suggestionKey
  useEffect(() => {
    if (!needsSuggestion) return
    let isCurrent = true
    const done = (suggestion: string) =>
      isCurrent && setSuggested({ key: suggestionKey, suggestion })
    // eslint-disable-next-line local/no-command-in-effect -- prefetch: a paid model call each time the editor's target (note type, deck, field, type) changes, even if the prompt step is never opened
    suggestPrompt({ deckId, fieldType, noteTypeId, targetFieldName })
      .then((result) => done(result.suggestion))
      .catch(() => done(""))
    return () => {
      isCurrent = false
    }
  }, [
    deckId,
    fieldType,
    needsSuggestion,
    noteTypeId,
    suggestionKey,
    targetFieldName,
  ])

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
        sourceFieldName: getFirstSourceField({
          deckId: nextTarget.deckId,
          globalDeckId: state.globalDeckId,
          ignoreFieldId: current.editingFieldId,
          noteType,
          smartFields: state.smartFields,
          targetFieldName: nextTarget.targetFieldName,
        }),
        target: nextTarget,
      }
    })
  }

  const generateDraftPrompt = async (description = form.writePrompt) => {
    if (form.target.fieldType === "tts" || description.trim() === "") {
      return false
    }

    update({ error: null, isGenerating: true })
    try {
      const result = await generatePrompt({
        noteTypeId: form.target.noteTypeId,
        deckId: form.target.deckId,
        targetFieldName: form.target.targetFieldName,
        fieldType: form.target.fieldType,
        generationPrompt: description,
      })
      update({ prompt: result.prompt })
      return true
    } catch (error) {
      update({
        error: errorMessage(error, t("fieldEditor.errors.writePrompt")),
      })
      return false
    } finally {
      update({ isGenerating: false })
    }
  }

  const save = async () => {
    const validationError = validateFieldEditorDraft(
      form,
      state.smartFields,
      state.globalDeckId,
    )
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
          void trackAnalyticsEvent({
            event: "smart_field_saved",
            properties: { field_type: form.target.fieldType },
          })
        }
        if (state.smartFields.length === 0) {
          useAppStore.setState({ firstFieldGuide: "new" })
        }
      }
      onClose()
    } catch (error) {
      update({
        error: errorMessage(error, t("fieldEditor.errors.save")),
        isSaving: false,
      })
    }
  }

  const markPromptTipSeen = async () => {
    try {
      await saveSettings({ ...state.settings, didSeeGeneratedPromptTip: true })
    } catch {
      // Harmless: the tip just shows once more next time.
    }
  }

  return {
    dismissError: () => update({ error: null }),
    form,
    generateDraftPrompt,
    markPromptTipSeen,
    save,
    setPinnedChat: (settings) => setPinned("chat", settings),
    setPinnedImage: (settings) => setPinned("image", settings),
    setPinnedTTS: (settings) => setPinned("tts", settings),
    setStep: (step) => update({ step }),
    setTarget: changeTarget,
    suggestion: suggested?.key === suggestionKey ? suggested.suggestion : null,
    update,
  }
}
