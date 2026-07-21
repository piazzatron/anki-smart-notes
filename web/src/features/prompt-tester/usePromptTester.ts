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

import { useAppStore } from "@/store/appStore"
import type { SelectedNote, Selection } from "@/types/api"

interface PromptTestResult<R> {
  cardId: number
  latencyMs: number
  prompt: string
  value: R
}

interface PromptTesterState<R> {
  error: string | null
  isTesting: boolean
  prompt: string
  result: PromptTestResult<R> | null
}

interface UsePromptTesterArgs<R> {
  fallbackError: string
  initialPrompt: string
  prompt?: string
  run: (args: { cardId: number; prompt: string }) => Promise<R>
}

export interface PromptTesterControls<R> {
  dismissError: () => void
  error: string | null
  isTesting: boolean
  prompt: string
  result: Omit<PromptTestResult<R>, "cardId"> | null
  runTest: () => Promise<void>
  selection: Selection | null
  selectedNote: SelectedNote | null
  setPrompt: (prompt: string) => void
}

export const getVisiblePromptTestResult = <R>(
  result: PromptTestResult<R> | null,
  selectedCardId: number | null,
): Omit<PromptTestResult<R>, "cardId"> | null => {
  if (result?.cardId !== selectedCardId) return null

  return {
    latencyMs: result.latencyMs,
    prompt: result.prompt,
    value: result.value,
  }
}

export const usePromptTester = <R>({
  fallbackError,
  initialPrompt,
  prompt: controlledPrompt,
  run,
}: UsePromptTesterArgs<R>): PromptTesterControls<R> => {
  const selection = useAppStore((store) => store.selection)
  const [tester, setTester] = useState<PromptTesterState<R>>({
    error: null,
    isTesting: false,
    prompt: initialPrompt,
    result: null,
  })
  const selectedNote = selection?.note ?? null
  const prompt = controlledPrompt ?? tester.prompt
  const visibleResult = getVisiblePromptTestResult(
    tester.result,
    selectedNote?.cardId ?? null,
  )
  const patchTester = (updates: Partial<PromptTesterState<R>>) =>
    setTester((current) => ({ ...current, ...updates }))

  const runTest = async () => {
    if (selectedNote === null) return

    patchTester({ error: null, isTesting: true })
    const startedAt = performance.now()
    try {
      const value = await run({ cardId: selectedNote.cardId, prompt })
      patchTester({
        result: {
          cardId: selectedNote.cardId,
          latencyMs: Math.max(1, Math.round(performance.now() - startedAt)),
          prompt,
          value,
        },
      })
    } catch (error) {
      patchTester({
        error: error instanceof Error ? error.message : fallbackError,
      })
    } finally {
      patchTester({ isTesting: false })
    }
  }

  return {
    dismissError: () => patchTester({ error: null }),
    error: tester.error,
    isTesting: tester.isTesting,
    prompt,
    result: visibleResult,
    runTest,
    selection,
    selectedNote,
    setPrompt: (prompt: string) => {
      if (controlledPrompt === undefined) patchTester({ prompt })
    },
  }
}
