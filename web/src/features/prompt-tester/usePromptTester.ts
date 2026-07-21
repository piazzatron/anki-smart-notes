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

import { testTextPrompt } from "@/services/commands"
import { useAppStore } from "@/store/appStore"
import type { ChatGenerationSettings } from "@/types/api"

interface PromptTestResult {
  cardId: number
  latencyMs: number
  model: string
  text: string
}

interface PromptTesterState {
  error: string | null
  isTesting: boolean
  prompt: string
  result: PromptTestResult | null
}

export const getVisiblePromptTestResult = (
  result: PromptTestResult | null,
  selectedCardId: number | null,
): PromptTestResult | null =>
  result?.cardId === selectedCardId ? result : null

export const usePromptTester = (settings: ChatGenerationSettings) => {
  const selection = useAppStore((store) => store.selection)
  const [tester, setTester] = useState<PromptTesterState>({
    error: null,
    isTesting: false,
    prompt: "Translate {{Expression}} into natural English.",
    result: null,
  })
  const selectedNote = selection?.note ?? null
  const visibleResult = getVisiblePromptTestResult(
    tester.result,
    selectedNote?.cardId ?? null,
  )
  const patchTester = (updates: Partial<PromptTesterState>) =>
    setTester((current) => ({ ...current, ...updates }))

  const runTest = async () => {
    if (selectedNote === null) return

    patchTester({ error: null, isTesting: true })
    const startedAt = performance.now()
    try {
      const result = await testTextPrompt({
        cardId: selectedNote.cardId,
        prompt: tester.prompt,
        settings,
      })
      patchTester({
        result: {
          cardId: selectedNote.cardId,
          latencyMs: Math.max(1, Math.round(performance.now() - startedAt)),
          model: settings.model,
          text: result.text,
        },
      })
    } catch (error) {
      patchTester({
        error:
          error instanceof Error ? error.message : "Could not test this prompt",
      })
    } finally {
      patchTester({ isTesting: false })
    }
  }

  return {
    dismissError: () => patchTester({ error: null }),
    error: tester.error,
    isTesting: tester.isTesting,
    prompt: tester.prompt,
    result: visibleResult,
    runTest,
    selection,
    selectedNote,
    setPrompt: (prompt: string) => patchTester({ prompt }),
  }
}
