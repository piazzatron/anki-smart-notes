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

interface DefaultsFormState<T> {
  draft: Partial<T> | null
  error: string | null
}

interface UseDefaultsFormArgs<T> {
  fallbackError: string
  save: (values: T) => Promise<void>
  serverDefaults: T
}

/** A defaults screen's settings. Every change is saved as it is made — there is nothing
 *  to confirm, so the screen shows the change immediately and the draft only stands in
 *  until the server state catches up. */
export const useDefaultsForm = <T extends object>({
  fallbackError,
  save: saveDefaults,
  serverDefaults,
}: UseDefaultsFormArgs<T>) => {
  const [form, setForm] = useState<DefaultsFormState<T>>({
    draft: null,
    error: null,
  })
  const values = { ...serverDefaults, ...form.draft }
  const patchForm = (updates: Partial<DefaultsFormState<T>>) =>
    setForm((current) => ({ ...current, ...updates }))

  const updateDefault = async (updates: Partial<T>) => {
    setForm((current) => ({
      draft: { ...current.draft, ...updates },
      error: null,
    }))
    try {
      await saveDefaults({ ...values, ...updates })
    } catch (error) {
      // Drop the draft on a failed save, so the screen never shows a setting the
      // server did not take.
      patchForm({
        draft: null,
        error: errorMessage(error, fallbackError),
      })
    }
  }

  return {
    dismissError: () => patchForm({ error: null }),
    form: { error: form.error, values },
    updateDefault,
  }
}
