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

interface DefaultsFormState<T> {
  draft: Partial<T> | null
  error: string | null
  isSaving: boolean
}

interface UseDefaultsFormArgs<T> {
  fallbackError: string
  save: (values: T) => Promise<void>
  serverDefaults: T
}

export const useDefaultsForm = <T extends object>({
  fallbackError,
  save: saveDefaults,
  serverDefaults,
}: UseDefaultsFormArgs<T>) => {
  const [form, setForm] = useState<DefaultsFormState<T>>({
    draft: null,
    error: null,
    isSaving: false,
  })
  const values = { ...serverDefaults, ...form.draft }
  const patchForm = (updates: Partial<DefaultsFormState<T>>) =>
    setForm((current) => ({ ...current, ...updates }))
  const patchDraft = (updates: Partial<T>) =>
    setForm((current) => ({
      ...current,
      draft: { ...current.draft, ...updates },
    }))

  const save = async () => {
    patchForm({ error: null, isSaving: true })
    try {
      await saveDefaults(values)
      patchForm({ draft: null })
    } catch (error) {
      patchForm({
        error: error instanceof Error ? error.message : fallbackError,
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
    patchDraft,
    save,
  }
}
