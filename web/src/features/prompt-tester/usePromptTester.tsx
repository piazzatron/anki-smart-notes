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

import { useEffect, useState, type ReactNode } from "react"

import { modelLabel } from "@/lib/catalog"
import { errorMessage } from "@/lib/errors"
import {
  testImagePrompt,
  testTextPrompt,
  testTTSPrompt,
} from "@/services/commands"
import { useAppStore } from "@/store/appStore"
import type {
  ChatGenerationSettings,
  ImageGenerationSettings,
  MediaTestResult,
  SelectedNote,
  Selection,
  TextPromptTestResult,
  TTSGenerationSettings,
  TTSMediaTestResult,
} from "@/types/api"

import { getMissingPromptFieldNames } from "./promptTestCard"
import { ResolvedPrompt } from "./PromptTestResultModal"

type TestValue = MediaTestResult | TextPromptTestResult | TTSMediaTestResult

interface TestRun {
  cardId: number | null
  latencyMs: number
  prompt: string
  value: TestValue
}

interface TesterState {
  error: string | null
  isTesting: boolean
  run: TestRun | null
}

export type PromptTesterArgs = {
  // Omitted when something else on the screen edits the prompt, in which case no
  // editor is offered here.
  onPromptChange?: (prompt: string) => void
  prompt: string
  requiredNoteTypeId?: number
} & (
  | { fieldType: "chat"; settings: ChatGenerationSettings }
  | { fieldType: "image"; settings: ImageGenerationSettings }
  | { fieldType: "tts"; settings: TTSGenerationSettings; voiceName: string }
)

/** One test, plus everything a screen needs to offer it and present what came back. */
export interface PromptTester {
  dismissError: () => void
  error: string | null
  hasNoteTypeMismatch: boolean
  isResultOpen: boolean
  isTesting: boolean
  prompt: string
  promptLabel: string
  provenance: string
  requiredNoteTypeId: number | null
  // What a finished run has to show. Voice has none: it plays instead.
  resultNode: ReactNode
  // Present only for a run against a card, which is the only run that can be saved.
  resultToken: string | null
  runTest: () => Promise<void>
  selectedNote: SelectedNote | null
  selection: Selection | null
  setError: (error: string) => void
  setIsResultOpen: (open: boolean) => void
  // Null when the caller edits the prompt elsewhere.
  setPrompt: ((prompt: string) => void) | null
  showResultModal: boolean
}

// Everything a test needs is here: which endpoint to call, what to say when it fails,
// and how to present what comes back. Build it once per screen and hand the same one to
// every place that offers to run it, so the picked card, the last result, the error and
// whether the result modal stands are shared rather than duplicated per Test button.
export const usePromptTester = (args: PromptTesterArgs): PromptTester => {
  const { fieldType, onPromptChange, prompt, requiredNoteTypeId } = args
  const [inheritedSelection] = useState(() => useAppStore.getState().selection)
  const [selection, setSelection] = useState(() =>
    getInitialPromptTestSelection({
      prompt,
      requiredNoteTypeId,
      selection: inheritedSelection,
    }),
  )
  const [state, setState] = useState<TesterState>({
    error: null,
    isTesting: false,
    run: null,
  })
  const [isResultOpen, setIsResultOpen] = useState(false)
  // Voice plays its result instead of presenting it, so it has no modal to open.
  const showResultModal = fieldType !== "tts"

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
  const run = getVisiblePromptTestResult(
    state.run,
    selectedNote?.cardId ?? null,
  )
  const resultValue = run?.value
  const patchState = (updates: Partial<TesterState>) =>
    setState((current) => ({ ...current, ...updates }))

  // Voice presents itself: a finished run plays at once rather than waiting behind a
  // "view result" affordance. Leaving the screen cuts it off mid-sentence.
  useEffect(() => {
    if (fieldType !== "tts" || resultValue === undefined) return
    if (!("dataUrl" in resultValue)) return

    const audio = new Audio(resultValue.dataUrl)
    void audio.play()
    return () => audio.pause()
  }, [fieldType, resultValue])

  const runTest = async () => {
    // A card of the wrong note type is the one selection worth refusing outright: its
    // fields are not the field's fields. A missing card is fine — see runDisabled.
    if (hasNoteTypeMismatch) return

    patchState({ error: null, isTesting: true })
    try {
      patchState({
        run: await runTimedTest({
          args,
          cardId: selectedNote?.cardId ?? null,
          prompt,
        }),
      })
      if (showResultModal) setIsResultOpen(true)
    } catch (error) {
      patchState({ error: errorMessage(error, FAILURES[fieldType]) })
    } finally {
      patchState({ isTesting: false })
    }
  }

  return {
    dismissError: () => patchState({ error: null }),
    error: state.error,
    hasNoteTypeMismatch,
    isResultOpen,
    isTesting: state.isTesting,
    prompt,
    promptLabel: fieldType === "tts" ? "Text to speak" : "Prompt",
    provenance:
      args.fieldType === "tts"
        ? args.voiceName
        : modelLabel(args.settings.model),
    requiredNoteTypeId: requiredNoteTypeId ?? null,
    resultNode: renderTestResult({ fieldType, run, selectedNote }),
    resultToken: resultValue?.resultToken ?? null,
    runTest,
    selectedNote,
    selection,
    // Failures of actions built on top of a result (saving it to the card) report
    // through the same dismissable banner as a failed run.
    setError: (error: string) => patchState({ error }),
    setIsResultOpen,
    setPrompt: onPromptChange ?? null,
    showResultModal,
  }
}

// A result belongs to the card it ran against, so picking another card drops it rather
// than showing output that describes a card no longer in front of the user.
export const getVisiblePromptTestResult = <R extends { cardId: number | null }>(
  run: R | null,
  selectedCardId: number | null,
): R | null => (run?.cardId !== selectedCardId ? null : run)

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

  // The picked note is returned even on a mismatch: the tester shows which card is
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

const FAILURES: Record<PromptTesterArgs["fieldType"], string> = {
  chat: "Could not test this prompt",
  image: "Could not generate an image",
  tts: "Could not generate audio",
}

// Timing lives out here rather than in the hook body, where reading the clock counts as
// an impure call.
const runTimedTest = async (args: {
  args: PromptTesterArgs
  cardId: number | null
  prompt: string
}): Promise<TestRun> => {
  const startedAt = performance.now()
  const value = await runTestForFieldType(args)

  return {
    cardId: args.cardId,
    latencyMs: Math.max(1, Math.round(performance.now() - startedAt)),
    prompt: args.prompt,
    value,
  }
}

// The card is optional everywhere: the server only needs one when the prompt reads
// fields off it, which is checked before the run is offered.
const runTestForFieldType = ({
  args,
  cardId,
  prompt,
}: {
  args: PromptTesterArgs
  cardId: number | null
  prompt: string
}): Promise<TestValue> => {
  const card = cardId ?? undefined
  if (args.fieldType === "chat") {
    return testTextPrompt({ cardId: card, prompt, settings: args.settings })
  }
  if (args.fieldType === "image") {
    return testImagePrompt({ cardId: card, prompt, settings: args.settings })
  }

  return testTTSPrompt({ cardId: card, settings: args.settings, text: prompt })
}

// What a finished run has to show. Voice returns nothing on purpose: it has already
// played by the time this is asked.
const renderTestResult = ({
  fieldType,
  run,
  selectedNote,
}: {
  fieldType: PromptTesterArgs["fieldType"]
  run: TestRun | null
  selectedNote: SelectedNote | null
}): ReactNode => {
  if (run === null) return null

  if ("text" in run.value) {
    return (
      <>
        <ResolvedPrompt note={selectedNote} prompt={run.prompt} />
        <p className="text-[13px] leading-[1.6] whitespace-pre-wrap text-zinc-100">
          {run.value.text}
        </p>
      </>
    )
  }

  if (fieldType !== "image") return null

  return (
    <GeneratedImage
      dataUrl={run.value.dataUrl}
      key={run.value.resultToken}
      note={selectedNote}
      prompt={run.prompt}
    />
  )
}

// Keyed by the run that produced it, so the reported size never describes the image
// from the previous run.
const GeneratedImage = ({
  dataUrl,
  note,
  prompt,
}: {
  dataUrl: string
  note: SelectedNote | null
  prompt: string
}) => {
  const [dimensions, setDimensions] = useState<{
    height: number
    width: number
  } | null>(null)

  return (
    <>
      <ResolvedPrompt note={note} prompt={prompt} />
      <img
        alt="Generated image preview"
        className="max-h-[50vh] w-full rounded-lg border border-white/[0.1] bg-black/20 object-contain"
        onLoad={(event) =>
          setDimensions({
            height: event.currentTarget.naturalHeight,
            width: event.currentTarget.naturalWidth,
          })
        }
        src={dataUrl}
      />
      {dimensions !== null && (
        <p className="mt-2 text-right text-[10.5px] text-ink-faint">
          {dimensions.width} × {dimensions.height}
        </p>
      )}
    </>
  )
}
