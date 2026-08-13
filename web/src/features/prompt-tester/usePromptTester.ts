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
import { useAppStore } from "@/store/appStore"

import { getMissingPromptFieldNames } from "./promptTestCard"
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
  requiredNoteTypeId?: number
  run: (args: { cardId: number; prompt: string }) => Promise<R>
}

export interface PromptTesterControls<R> {
  dismissError: () => void
  error: string | null
  hasNoteTypeMismatch: boolean
  // True when this tester owns its prompt rather than being handed one, so whoever
  // renders it may offer an editor for it.
  isPromptEditable: boolean
  isTesting: boolean
  prompt: string
  requiredNoteTypeId: number | null
  result: Omit<PromptTestResult<R>, "cardId"> | null
  runTest: () => Promise<void>
  selection: Selection | null
  selectedNote: SelectedNote | null
  setError: (error: string) => void
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

export const getPromptTestSelection = (
  selection: Selection | null,
  requiredNoteTypeId?: number,
): {
  hasNoteTypeMismatch: boolean
  selectedNote: SelectedNote | null
} => {
  const selectedNote = selection?.note ?? null
  const hasNoteTypeMismatch =
    selectedNote !== null &&
    requiredNoteTypeId !== undefined &&
    selectedNote.noteTypeId !== requiredNoteTypeId

  // The picked note is returned even on a mismatch: the panel shows which card is
  // selected and why it can't run. Running is gated separately.
  return { hasNoteTypeMismatch, selectedNote }
}

// A card picked before this tester opened was not picked for it. If the prompt cannot
// run against that card, ask for one instead of complaining about it — only a card
// picked while the tester is open is an answer to the tester.
export const getInitialPromptTestSelection = ({
  prompt,
  requiredNoteTypeId,
  selection,
}: {
  prompt: string
  requiredNoteTypeId?: number
  selection: Selection | null
}): Selection | null => {
  const { hasNoteTypeMismatch, selectedNote } = getPromptTestSelection(
    selection,
    requiredNoteTypeId,
  )
  if (hasNoteTypeMismatch) return null
  if (
    selectedNote !== null &&
    getMissingPromptFieldNames(prompt, selectedNote).length > 0
  ) {
    return null
  }

  return selection
}

export const usePromptTester = <R>({
  fallbackError,
  initialPrompt,
  prompt: controlledPrompt,
  requiredNoteTypeId,
  run,
}: UsePromptTesterArgs<R>): PromptTesterControls<R> => {
  const [inheritedSelection] = useState(() => useAppStore.getState().selection)
  const [selection, setSelection] = useState(() =>
    getInitialPromptTestSelection({
      prompt: controlledPrompt ?? initialPrompt,
      requiredNoteTypeId,
      selection: inheritedSelection,
    }),
  )
  const [tester, setTester] = useState<PromptTesterState<R>>({
    error: null,
    isTesting: false,
    prompt: initialPrompt,
    result: null,
  })

  useEffect(() => {
    // The retained SSE value predates this tester. Once the store receives a new
    // selection object, every selection is live user feedback and stays unfiltered.
    return useAppStore.subscribe((store, previousStore) => {
      if (store.selection !== previousStore.selection) {
        setSelection(store.selection)
      }
    })
  }, [])

  const { hasNoteTypeMismatch, selectedNote } = getPromptTestSelection(
    selection,
    requiredNoteTypeId,
  )
  const prompt = controlledPrompt ?? tester.prompt
  const visibleResult = getVisiblePromptTestResult(
    tester.result,
    selectedNote?.cardId ?? null,
  )
  const patchTester = (updates: Partial<PromptTesterState<R>>) =>
    setTester((current) => ({ ...current, ...updates }))

  const runTest = async () => {
    if (selectedNote === null || hasNoteTypeMismatch) return

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
        error: errorMessage(error, fallbackError),
      })
    } finally {
      patchTester({ isTesting: false })
    }
  }

  return {
    dismissError: () => patchTester({ error: null }),
    error: tester.error,
    hasNoteTypeMismatch,
    isPromptEditable: controlledPrompt === undefined,
    isTesting: tester.isTesting,
    prompt,
    requiredNoteTypeId: requiredNoteTypeId ?? null,
    result: visibleResult,
    runTest,
    selection,
    selectedNote,
    // Failures of actions built on top of a result (saving it to the card) report
    // through the same dismissable banner as a failed run.
    setError: (error: string) => patchTester({ error }),
    setPrompt: (prompt: string) => {
      if (controlledPrompt === undefined) patchTester({ prompt })
    },
  }
}
