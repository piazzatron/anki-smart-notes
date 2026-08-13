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

import { Check, LoaderCircle, Play } from "lucide-react"
import { useId, useState, type ReactNode } from "react"

import { ValidPromptFields } from "@/components/shared/ValidPromptFields"
import { Button } from "@/components/ui/Button"
import { ErrorBanner } from "@/components/ui/ErrorBanner"
import { errorMessage } from "@/lib/errors"
import { getValidPromptFields } from "@/lib/promptFields"
import { saveTestResultToCard } from "@/services/commands"
import { useAppStore } from "@/store/appStore"

import {
  getSaveTestResultTarget,
  usePromptTestCardState,
} from "./promptTestCard"
import { PromptTestResultModal } from "./PromptTestResultModal"
import { SelectedTestCard } from "./SelectedTestCard"
import type { PromptTesterControls } from "./usePromptTester"

interface PromptTesterStripProps<R extends { resultToken: string }> {
  children: ReactNode
  promptLabel: string
  provenance: string
  // Only a tester bound to a Smart Field can write its result back to the card.
  saveTargetFieldName?: string
  tester: PromptTesterControls<R>
  title: string
}

// The one tester: a titled zone with the card to run against and an always-present Test
// button, plus the prompt itself where nothing else on the screen owns it. The result is
// never shown here — it opens in a modal, and stays reachable through "View result".
export const PromptTesterStrip = <R extends { resultToken: string }>({
  children,
  promptLabel,
  provenance,
  saveTargetFieldName,
  tester,
  title,
}: PromptTesterStripProps<R>) => {
  const noteTypes = useAppStore((store) => store.state?.noteTypes ?? null)
  const smartFields = useAppStore((store) => store.state?.smartFields ?? null)
  const promptFieldId = useId()
  const card = usePromptTestCardState(tester)
  const [isResultOpen, setIsResultOpen] = useState(false)
  const hasResult = tester.result !== null && tester.selectedNote !== null
  const saveTarget =
    saveTargetFieldName === undefined ||
    tester.result === null ||
    tester.selectedNote === null
      ? null
      : getSaveTestResultTarget({
          fieldName: saveTargetFieldName,
          selectedNote: tester.selectedNote,
          token: tester.result.value.resultToken,
        })
  // A failed run leaves nothing to show, and picking another card drops the result, so
  // the modal only stands while there is a result (or one on the way).
  const isResultVisible = isResultOpen && (hasResult || tester.isTesting)

  const runTestAndShowResult = async () => {
    await tester.runTest()
    setIsResultOpen(true)
  }

  return (
    <div className="w-full">
      <h2 className="mb-2.5 text-[15px] leading-tight font-semibold text-zinc-100">
        {title}
      </h2>

      {!isResultVisible && tester.error !== null && (
        <ErrorBanner
          className="mb-3"
          message={tester.error}
          onDismiss={tester.dismissError}
        />
      )}

      {/* Nothing above this tester owns the prompt, so it does. The fields it may
          reference are those of the card currently picked in the browser. */}
      {tester.isPromptEditable && (
        <div className="mb-3">
          <label
            className="mb-1.5 block text-[11px] text-ink-muted"
            htmlFor={promptFieldId}
          >
            {promptLabel}
          </label>
          <textarea
            className="min-h-16 w-full resize-y rounded-md border border-white/10 bg-white/[0.03] px-3 py-2.5 font-mono text-[12px] leading-[1.55] text-zinc-200 transition outline-none placeholder:text-zinc-700 focus:border-indigo/45"
            id={promptFieldId}
            onChange={(event) => tester.setPrompt(event.target.value)}
            rows={2}
            value={tester.prompt}
          />
          <ValidPromptFields
            fieldNames={getValidPromptFields({
              deckId: tester.selectedNote?.deckId ?? 0,
              noteType: noteTypes?.find(
                (noteType) => noteType.id === tester.selectedNote?.noteTypeId,
              ),
              smartFields: smartFields ?? [],
            })}
          />
        </div>
      )}

      <div className="flex items-center gap-3">
        <div className="min-w-0 flex-1">
          <SelectedTestCard
            compact
            compactAction={
              hasResult && !isResultVisible ? (
                <button
                  className="shrink-0 cursor-pointer text-[11px] text-indigo-soft transition hover:text-indigo-soft/80"
                  onClick={() => setIsResultOpen(true)}
                >
                  View result
                </button>
              ) : undefined
            }
            deckName={card.deckName}
            missingFieldNames={card.missingFieldNames}
            note={tester.selectedNote}
            noteTypeName={card.noteTypeName}
            referencedFieldNames={card.referencedFieldNames}
            requiredNoteTypeName={card.requiredNoteTypeName}
            selection={tester.selection}
            showNoteTypeMismatch={tester.hasNoteTypeMismatch}
          />
        </div>

        <Button
          className="h-[54px] shrink-0 px-4 text-[12.5px] disabled:cursor-default disabled:opacity-40"
          disabled={card.runDisabled}
          onClick={() => void runTestAndShowResult()}
        >
          {tester.isTesting ? (
            <LoaderCircle aria-hidden className="size-3.5 animate-spin" />
          ) : (
            <Play aria-hidden className="size-3.5 fill-current" />
          )}
          {tester.isTesting ? "Testing…" : "Test"}
        </Button>
      </div>

      {/* Always mounted, so the dialog can animate itself out on close. */}
      <PromptTestResultModal
        onClose={() => setIsResultOpen(false)}
        open={isResultVisible}
        provenance={provenance}
        saveAction={
          saveTarget === null ? null : (
            // Keyed by token: a new run mints a new one, and the previous save no
            // longer describes what is shown.
            <SaveResultButton
              cardId={saveTarget.cardId}
              fieldName={saveTarget.fieldName}
              key={saveTarget.token}
              onError={tester.setError}
              token={saveTarget.token}
            />
          )
        }
        tester={tester}
      >
        {children}
      </PromptTestResultModal>
    </div>
  )
}

interface SaveResultButtonProps {
  cardId: number
  fieldName: string
  onError: (error: string) => void
  token: string
}

// Writes the shown result into the card the test ran against. The plugin keeps only the
// newest test artifact, so a save can come back expired — that reads as a run error.
export const SaveResultButton = ({
  cardId,
  fieldName,
  onError,
  token,
}: SaveResultButtonProps) => {
  const [status, setStatus] = useState<"idle" | "saving" | "saved">("idle")

  const save = async () => {
    setStatus("saving")
    try {
      await saveTestResultToCard({ cardId, fieldName, token })
      setStatus("saved")
    } catch (error) {
      setStatus("idle")
      onError(errorMessage(error, "Could not save this result to the card"))
    }
  }

  return (
    <Button
      disabled={status !== "idle"}
      onClick={() => void save()}
      variant="success"
    >
      {status === "saving" && (
        <LoaderCircle aria-hidden className="size-3.5 animate-spin" />
      )}
      {status === "saved" && <Check aria-hidden className="size-3.5" />}
      {status === "saved"
        ? `Saved to ${fieldName}`
        : status === "saving"
          ? "Saving…"
          : "Save to card"}
    </Button>
  )
}
