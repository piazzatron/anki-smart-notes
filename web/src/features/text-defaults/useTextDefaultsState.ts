import { useEffect, useRef, useState } from "react"

import { saveChatDefaults, testTextPrompt } from "@/services/commands"
import type { AppState } from "@/types/api"

import { textDefaultsMatch } from "./textDefaults"

interface UseTextDefaultsStateArgs {
  serverDefaults: AppState["defaults"]["chat"]
}

interface TextTestResult {
  cardId: number
  latencyMs: number
  model: string
  text: string
}

interface TextDefaultsFormState {
  draft: AppState["defaults"]["chat"]
  error: string | null
  isSaving: boolean
  isTesting: boolean
  prompt: string
  result: TextTestResult | null
}

export const useTextDefaultsState = ({
  serverDefaults,
}: UseTextDefaultsStateArgs) => {
  const [form, setForm] = useState<TextDefaultsFormState>(() => ({
    draft: serverDefaults,
    error: null,
    isSaving: false,
    isTesting: false,
    prompt: "Translate {{Expression}} into natural English.",
    result: null,
  }))
  const previousServerDefaults = useRef(serverDefaults)
  const patch = (updates: Partial<TextDefaultsFormState>) =>
    setForm((current) => ({ ...current, ...updates }))

  useEffect(() => {
    setForm((current) => ({
      ...current,
      draft: textDefaultsMatch(current.draft, previousServerDefaults.current)
        ? serverDefaults
        : current.draft,
    }))
    previousServerDefaults.current = serverDefaults
  }, [serverDefaults])

  const save = async () => {
    patch({ error: null, isSaving: true })
    try {
      await saveChatDefaults(form.draft)
    } catch (error) {
      patch({
        error:
          error instanceof Error
            ? error.message
            : "Could not save text defaults",
      })
    } finally {
      patch({ isSaving: false })
    }
  }

  const runTest = async (cardId: number) => {
    patch({ error: null, isTesting: true })
    const startedAt = performance.now()
    try {
      const result = await testTextPrompt({
        cardId,
        prompt: form.prompt,
        settings: form.draft,
      })
      patch({
        result: {
          cardId,
          latencyMs: Math.max(1, Math.round(performance.now() - startedAt)),
          model: form.draft.model,
          text: result.text,
        },
      })
    } catch (error) {
      patch({
        error:
          error instanceof Error ? error.message : "Could not test this prompt",
      })
    } finally {
      patch({ isTesting: false })
    }
  }

  return {
    cancel: () => patch({ draft: serverDefaults }),
    dismissError: () => patch({ error: null }),
    form,
    hasPendingChanges: !textDefaultsMatch(form.draft, serverDefaults),
    patchDraft: (updates: Partial<AppState["defaults"]["chat"]>) =>
      patch({ draft: { ...form.draft, ...updates } }),
    runTest,
    save,
    setPrompt: (prompt: string) => patch({ prompt }),
  }
}
