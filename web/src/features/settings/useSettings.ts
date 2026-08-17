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
import { saveSettings } from "@/services/commands"
import type { Settings } from "@/types/api"

interface SettingsFormState {
  draft: Settings | null
  error: string | null
  isSaving: boolean
}

export const useSettings = (serverSettings: Settings) => {
  const [form, setForm] = useState<SettingsFormState>({
    draft: null,
    error: null,
    isSaving: false,
  })
  const values = form.draft ?? serverSettings
  const patch = (partial: Partial<SettingsFormState>) =>
    setForm((current) => ({ ...current, ...partial }))

  const update = async (partial: Partial<Settings>) => {
    const next = { ...values, ...partial }
    patch({ draft: next, error: null, isSaving: true })
    try {
      await saveSettings(next)
      patch({ draft: null })
    } catch (error) {
      patch({
        error: errorMessage(error, "Could not save settings"),
      })
    } finally {
      patch({ isSaving: false })
    }
  }

  return {
    dismissError: () => patch({ error: null }),
    error: form.error,
    isSaving: form.isSaving,
    update,
    values,
  }
}
