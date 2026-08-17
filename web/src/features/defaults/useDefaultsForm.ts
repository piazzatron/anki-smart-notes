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

import { errorMessage } from "@/lib/errors"

interface DefaultsFormState<T> {
  draft: Partial<T> | null
  error: string | null
  isSaving: boolean
}

interface UseDefaultsFormArgs<T> {
  fallbackError: string
  onDirtyChange?: (isDirty: boolean) => void
  save: (values: T) => Promise<void>
  serverDefaults: T
}

/** Keeps defaults edits local until the user explicitly saves them. */
export const useDefaultsForm = <T extends object>({
  fallbackError,
  onDirtyChange,
  save: saveDefaults,
  serverDefaults,
}: UseDefaultsFormArgs<T>) => {
  const [form, setForm] = useState<DefaultsFormState<T>>({
    draft: null,
    error: null,
    isSaving: false,
  })
  const values = { ...serverDefaults, ...form.draft }
  const isDirty = !defaultsMatch(values, serverDefaults)
  const patchForm = (updates: Partial<DefaultsFormState<T>>) =>
    setForm((current) => ({ ...current, ...updates }))

  useEffect(() => {
    onDirtyChange?.(isDirty)

    return () => onDirtyChange?.(false)
  }, [isDirty, onDirtyChange])

  const updateDefault = (updates: Partial<T>) => {
    setForm((current) => ({
      ...current,
      draft: { ...current.draft, ...updates },
      error: null,
    }))
  }

  const saveChanges = async () => {
    if (!isDirty || form.isSaving) return

    patchForm({ error: null, isSaving: true })
    try {
      await saveDefaults(values)
      patchForm({ draft: null, isSaving: false })
    } catch (error) {
      patchForm({
        error: errorMessage(error, fallbackError),
        isSaving: false,
      })
    }
  }

  return {
    dismissError: () => patchForm({ error: null }),
    form: {
      error: form.error,
      isDirty,
      isSaving: form.isSaving,
      values,
    },
    saveChanges,
    updateDefault,
  }
}

const defaultsMatch = <T extends object>(left: T, right: T): boolean => {
  const keys = new Set([...Object.keys(left), ...Object.keys(right)])

  return [...keys].every(
    (key) => left[key as keyof T] === right[key as keyof T],
  )
}
