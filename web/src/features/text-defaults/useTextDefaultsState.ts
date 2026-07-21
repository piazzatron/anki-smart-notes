import { useState } from "react"

import { saveChatDefaults } from "@/services/commands"
import type { AppState, ChatGenerationSettings } from "@/types/api"

interface UseTextDefaultsStateArgs {
  serverDefaults: AppState["defaults"]["chat"]
}

interface TextDefaultsFormState {
  draft: Partial<ChatGenerationSettings> | null
  error: string | null
  isSaving: boolean
}

export const useTextDefaultsState = ({
  serverDefaults,
}: UseTextDefaultsStateArgs) => {
  const [form, setForm] = useState<TextDefaultsFormState>(() => ({
    draft: null,
    error: null,
    isSaving: false,
  }))
  const values = { ...serverDefaults, ...form.draft }
  const patchForm = (updates: Partial<TextDefaultsFormState>) =>
    setForm((current) => ({ ...current, ...updates }))
  const patch = (updates: Partial<ChatGenerationSettings>) =>
    setForm((current) => ({
      ...current,
      draft: { ...current.draft, ...updates },
    }))

  const save = async () => {
    patchForm({ error: null, isSaving: true })
    try {
      await saveChatDefaults(values)
      patchForm({ draft: null })
    } catch (error) {
      patchForm({
        error:
          error instanceof Error
            ? error.message
            : "Could not save text defaults",
      })
    } finally {
      patchForm({ isSaving: false })
    }
  }

  return {
    cancel: () => patchForm({ draft: null }),
    dismissError: () => patchForm({ error: null }),
    form: { error: form.error, isSaving: form.isSaving, values },
    hasPendingChanges: form.draft !== null,
    patchDraft: patch,
    save,
  }
}
