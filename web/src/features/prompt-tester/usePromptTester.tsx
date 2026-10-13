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

import i18next from "i18next"
import { useEffect, useState, type ReactNode } from "react"
import { useTranslation } from "react-i18next"

import {
  IMAGE_MODEL_SWITCHES,
  getImageModelFamily,
  isSwitchOn,
} from "@/features/image-generation/imageModelFamilies"

import { modelLabel } from "@/lib/catalog"
import { errorMessage } from "@/lib/errors"
import {
  pickRandomTestCard,
  testImagePrompt,
  testTextPrompt,
  testTTSPrompt,
} from "@/services/commands"
import { useAppStore } from "@/store/appStore"
import type {
  ChatGenerationSettings,
  ImageGenerationSettings,
  MediaTestResult,
  NoteType,
  RandomTestCardArgs,
  SelectedNote,
  Selection,
  TextPromptTestResult,
  TTSGenerationSettings,
  TTSMediaTestResult,
} from "@/types/api"

import { resolvePromptReferences } from "./resolvePromptReferences"
import { ResolvedPrompt } from "./PromptTestResultModal"

type TestValue = MediaTestResult | TextPromptTestResult | TTSMediaTestResult

/** What a test ran with: the model or voice, plus any GPT Image 2.5 extras. */
export interface Provenance {
  extras: string[]
  primary: string
}

export interface TestRun {
  cardId: number | null
  id: number
  latencyMs: number
  prompt: string
  // Captured at run time so later settings changes don't relabel the result.
  provenance: Provenance
  value: TestValue
}

interface TesterState {
  error: string | null
  isTesting: boolean
  // Newest first, capped at MAX_SESSION_RUNS.
  runs: TestRun[]
  // Null shows the newest run.
  viewedRunId: number | null
}

// Images run a few MB each as data URLs, so the session keeps only the recent ones.
const MAX_SESSION_RUNS = 8

export type PromptTesterArgs = {
  // The deck the field generates for. With requiredNoteTypeId, the tester starts on a
  // random card from it when no usable card is picked.
  deckId?: number
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
  fieldType: PromptTesterArgs["fieldType"]
  hasNoteTypeMismatch: boolean
  // Earlier image results for the picked card this session, newest first.
  imageHistory: TestRun[]
  // The shown result is an earlier run, which the plugin no longer keeps to save.
  isEarlierRun: boolean
  isResultOpen: boolean
  isTesting: boolean
  prompt: string
  promptLabel: string
  provenance: Provenance | null
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
  viewRun: (runId: number) => void
}

// Everything a test needs is here: which endpoint to call, what to say when it fails,
// and how to present what comes back. Build it once per screen and hand the same one to
// every place that offers to run it, so the picked card, the last result, the error and
// whether the result modal stands are shared rather than duplicated per Test button.
export const usePromptTester = (args: PromptTesterArgs): PromptTester => {
  const { t } = useTranslation()
  const { deckId, fieldType, onPromptChange, prompt, requiredNoteTypeId } = args
  const [inheritedSelection] = useState(() => useAppStore.getState().selection)
  const [initialSelection] = useState(() =>
    getInitialPromptTestSelection({
      prompt,
      requiredNoteTypeId,
      selection: inheritedSelection,
    }),
  )
  const [selection, setSelection] = useState(initialSelection)
  const [randomCardArgs] = useState(() =>
    getRandomTestCardArgs({
      deckId,
      initialSelection,
      noteTypes: useAppStore.getState().state?.noteTypes ?? [],
      prompt,
      requiredNoteTypeId,
    }),
  )
  const [state, setState] = useState<TesterState>({
    error: null,
    isTesting: false,
    runs: [],
    viewedRunId: null,
  })
  const [isResultOpen, setIsResultOpen] = useState(false)
  // Voice plays its result instead of presenting it, so it has no modal to open.
  const showResultModal = fieldType !== "tts"

  // The voice tester's prompt is one of the picked card's fields, so a new card starts
  // it fresh. Typed prompts are kept across card picks.
  const resetsPromptOnCardPick = fieldType === "tts"

  useEffect(() => {
    // A voice screen mounted after the card was picked should also start fresh.
    if (resetsPromptOnCardPick && inheritedSelection?.note != null) {
      onPromptChange?.("")
    }

    // The retained SSE value predates this tester. Once the store receives a new
    // selection object, every selection is live user feedback and stays unfiltered.
    return useAppStore.subscribe((store, previousStore) => {
      if (store.selection !== previousStore.selection) {
        setSelection(store.selection)

        if (resetsPromptOnCardPick && store.selection?.note != null) {
          onPromptChange?.("")
        }
      }
    })
  }, [inheritedSelection, onPromptChange, resetsPromptOnCardPick])

  // A random card is only a starting point: a card picked in the Browser meanwhile wins.
  useEffect(() => {
    if (randomCardArgs === null) return

    let isCurrent = true
    pickRandomTestCard(randomCardArgs)
      .then((randomSelection) => {
        if (!isCurrent || randomSelection.note === null) return
        setSelection((current) =>
          current === initialSelection ? randomSelection : current,
        )
      })
      // Best effort: the tester still offers the Browser.
      .catch(() => undefined)
    return () => {
      isCurrent = false
    }
  }, [initialSelection, randomCardArgs])

  const { hasNoteTypeMismatch, selectedNote } = getPromptTestSelection(
    selection,
    requiredNoteTypeId,
  )
  const { history, isNewestRun, run } = selectPromptTestRuns({
    runs: state.runs,
    selectedCardId: selectedNote?.cardId ?? null,
    viewedRunId: state.viewedRunId,
  })
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
      const newRun = await runTimedTest({
        args,
        cardId: selectedNote?.cardId ?? null,
        prompt,
      })
      setState((current) => ({
        ...current,
        runs: [newRun, ...current.runs].slice(0, MAX_SESSION_RUNS),
        viewedRunId: null,
      }))
      if (showResultModal) setIsResultOpen(true)
    } catch (error) {
      patchState({ error: errorMessage(error, t(FAILURES[fieldType])) })
    } finally {
      patchState({ isTesting: false })
    }
  }

  return {
    dismissError: () => patchState({ error: null }),
    error: state.error,
    fieldType,
    hasNoteTypeMismatch,
    imageHistory: fieldType === "image" ? history : [],
    isEarlierRun: run !== null && !isNewestRun,
    isResultOpen,
    isTesting: state.isTesting,
    prompt,
    promptLabel:
      fieldType === "tts" ? t("promptTester.textToSpeak") : t("common.prompt"),
    provenance: run?.provenance ?? null,
    requiredNoteTypeId: requiredNoteTypeId ?? null,
    resultNode: renderTestResult({ fieldType, run, selectedNote }),
    // The plugin keeps only the newest result, so an earlier one can't be saved.
    resultToken: isNewestRun ? (resultValue?.resultToken ?? null) : null,
    runTest,
    selectedNote,
    selection,
    // Failures of actions built on top of a result (saving it to the card) report
    // through the same dismissable banner as a failed run.
    setError: (error: string) => patchState({ error }),
    setIsResultOpen,
    setPrompt: onPromptChange ?? null,
    showResultModal,
    viewRun: (runId: number) => {
      patchState({ viewedRunId: runId })
      setIsResultOpen(true)
    },
  }
}

// A result belongs to the card it ran against, so picking another card hides it rather
// than showing output that describes a card no longer in front of the user. Only the
// newest run overall can still be saved: the plugin keeps just that one.
export const selectPromptTestRuns = <
  R extends { cardId: number | null; id: number },
>({
  runs,
  selectedCardId,
  viewedRunId,
}: {
  runs: R[]
  selectedCardId: number | null
  viewedRunId: number | null
}): { history: R[]; isNewestRun: boolean; run: R | null } => {
  const history = runs.filter((run) => run.cardId === selectedCardId)
  const run =
    history.find((candidate) => candidate.id === viewedRunId) ??
    history[0] ??
    null

  return { history, isNewestRun: run !== null && run === runs[0], run }
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
    resolvePromptReferences(prompt, selectedNote.fields).missingFieldNames
      .length > 0
  ) {
    return null
  }

  return selection
}

// With no usable card picked, a field tester starts on a random card of its note type,
// preferring one whose prompt fields are filled in so the first test reads real content.
export const getRandomTestCardArgs = ({
  deckId,
  initialSelection,
  noteTypes,
  prompt,
  requiredNoteTypeId,
}: {
  deckId?: number
  initialSelection: Selection | null
  noteTypes: NoteType[]
  prompt: string
  requiredNoteTypeId?: number
}): RandomTestCardArgs | null => {
  if (initialSelection?.note != null) return null
  if (requiredNoteTypeId === undefined || deckId === undefined) return null

  const noteType = noteTypes.find((item) => item.id === requiredNoteTypeId)
  const fields = Object.fromEntries(
    (noteType?.fields ?? []).map((fieldName) => [fieldName, ""]),
  )

  return {
    deckId,
    filledFieldNames: resolvePromptReferences(
      prompt,
      fields,
    ).referencedFields.map(([fieldName]) => fieldName),
    noteTypeId: requiredNoteTypeId,
  }
}

const FAILURES: Record<PromptTesterArgs["fieldType"], string> = {
  chat: "promptTester.errors.testPrompt",
  image: "promptTester.errors.generateImage",
  tts: "promptTester.errors.generateAudio",
}

let nextRunId = 1

// Timing lives out here rather than in the hook body, where reading the clock counts as
// an impure call.
const runTimedTest = async (args: {
  args: PromptTesterArgs
  cardId: number | null
  prompt: string
}): Promise<TestRun> => {
  const provenance = getProvenance(args.args)
  const startedAt = performance.now()
  const value = await runTestForFieldType(args)

  return {
    cardId: args.cardId,
    id: nextRunId++,
    latencyMs: Math.max(1, Math.round(performance.now() - startedAt)),
    prompt: args.prompt,
    provenance,
    value,
  }
}

const getProvenance = (args: PromptTesterArgs): Provenance => {
  if (args.fieldType === "tts") return { extras: [], primary: args.voiceName }

  const { model } = args.settings
  const family = args.fieldType === "image" ? getImageModelFamily(model) : null
  const extras =
    family === null
      ? []
      : family.switches
          .filter((key) => isSwitchOn(family, model, key))
          .map((key) => i18next.t(IMAGE_MODEL_SWITCHES[key].label))
  return { extras, primary: modelLabel(model) }
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
        <p className="cursor-text text-[13px] leading-[1.6] whitespace-pre-wrap text-zinc-100 select-text">
          {run.value.text}
        </p>
      </>
    )
  }

  if (fieldType !== "image") return null

  return (
    <GeneratedImage
      dataUrl={run.value.dataUrl}
      latencyMs={run.latencyMs}
      note={selectedNote}
      prompt={run.prompt}
    />
  )
}

const GeneratedImage = ({
  dataUrl,
  latencyMs,
  note,
  prompt,
}: {
  dataUrl: string
  latencyMs: number
  note: SelectedNote | null
  prompt: string
}) => {
  const { t } = useTranslation()

  // Shrinks to the image's rendered width, so the prompt above and the timing below
  // share the picture's edges whatever its size. The width cap is the result dialog's
  // inner width (padding and border included); a percentage would collapse this
  // shrink-to-fit wrapper.
  return (
    <div className="mx-auto w-min">
      <ResolvedPrompt note={note} prompt={prompt} />
      <img
        alt={t("promptTester.generatedImagePreview")}
        className="block max-h-[56vh] w-auto max-w-[min(478px,calc(92vw-42px))] rounded-lg"
        src={dataUrl}
      />
      <p className="mt-2 text-right text-[10.5px] text-ink-faint">
        {t("promptTester.generatedIn", {
          seconds: (latencyMs / 1000).toFixed(1),
        })}
      </p>
    </div>
  )
}
