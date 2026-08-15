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
import { useId, useState } from "react"

import { Button } from "@/components/ui/Button"
import { ErrorBanner } from "@/components/ui/ErrorBanner"
import { errorMessage } from "@/lib/errors"
import { saveTestResultToCard } from "@/services/commands"

import {
  getSaveTestResultTarget,
  usePromptTestCardState,
} from "./promptTestCard"
import { PromptTestResultModal } from "./PromptTestResultModal"
import { SelectedTestCard } from "./SelectedTestCard"
import type { PromptTester } from "./usePromptTester"

interface PromptTesterStripProps {
  field: PromptTester
  // Only a tester bound to a Smart Field can write its result back to the card.
  saveTargetFieldName?: string
  title?: string
}

// The one tester: a titled zone with the card to run against and an always-present Test
// button, plus the prompt itself where nothing else on the screen owns it. Text and image
// results open in a modal; voice results play without presenting another surface.
export const PromptTesterStrip = ({
  field,
  saveTargetFieldName,
  title,
}: PromptTesterStripProps) => {
  const promptFieldId = useId()
  const { isResultOpen, setIsResultOpen, showResultModal } = field
  const card = usePromptTestCardState(field)
  // Only a run with something to show counts: a failed one leaves the node null.
  const hasResult = field.resultNode !== null
  const saveTarget =
    saveTargetFieldName === undefined ||
    field.resultToken === null ||
    field.selectedNote === null
      ? null
      : getSaveTestResultTarget({
          fieldName: saveTargetFieldName,
          selectedNote: field.selectedNote,
          token: field.resultToken,
        })
  // A failed run leaves nothing to show, and picking another card drops the result, so
  // the modal only stands while there is a result (or one on the way).
  const isResultVisible = isResultOpen && (hasResult || field.isTesting)

  return (
    <div className="w-full">
      {title !== undefined && (
        <h2 className="mb-2.5 text-[15px] leading-tight font-semibold text-zinc-100">
          {title}
        </h2>
      )}

      {!isResultVisible && field.error !== null && (
        <ErrorBanner
          className="mb-3"
          message={field.error}
          onDismiss={field.dismissError}
        />
      )}

      {/* Nothing above this tester owns the prompt, so it does. */}
      {field.setPrompt !== null && (
        <div className="group mb-3">
          <div className="mb-1.5 flex min-w-0 items-center gap-3 text-[11px]">
            <label className="shrink-0 text-ink-muted" htmlFor={promptFieldId}>
              {field.promptLabel}
            </label>
            {field.selectedNote !== null && (
              <p className="invisible min-w-0 flex-1 truncate text-left font-mono text-indigo-soft group-focus-within:visible">
                <span className="font-sans">Reference fields with: </span>
                {Object.keys(field.selectedNote.fields)
                  .map((fieldName) => `{{${fieldName}}}`)
                  .join(" · ")}
              </p>
            )}
          </div>
          <textarea
            className="min-h-16 w-full resize-y rounded-md border border-white/10 bg-white/[0.03] px-3 py-2.5 font-mono text-[12px] leading-[1.55] text-zinc-200 transition outline-none placeholder:text-zinc-700 focus:border-indigo/45"
            id={promptFieldId}
            onChange={(event) => field.setPrompt?.(event.target.value)}
            rows={2}
            value={field.prompt}
          />
        </div>
      )}

      <div className="flex h-[54px] items-stretch gap-3">
        <div className="min-w-0 flex-1">
          <SelectedTestCard
            compact
            compactAction={
              showResultModal && hasResult && !isResultVisible ? (
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
            note={field.selectedNote}
            noteTypeName={card.noteTypeName}
            referencedFieldNames={card.referencedFieldNames}
            requiredNoteTypeName={card.requiredNoteTypeName}
            selection={field.selection}
            showNoteTypeMismatch={field.hasNoteTypeMismatch}
          />
        </div>
        <PromptTestButton
          className="h-[54px] shrink-0 px-4 text-[12.5px]"
          field={field}
        />
      </div>

      {showResultModal && (
        // Kept mounted while enabled so the dialog can animate itself out on close.
        <PromptTestResultModal
          onClose={() => setIsResultOpen(false)}
          open={isResultVisible}
          provenance={field.provenance}
          saveAction={
            saveTarget === null ? null : (
              // Keyed by token: a new run mints a new one, and the previous save no
              // longer describes what is shown.
              <SaveResultButton
                cardId={saveTarget.cardId}
                fieldName={saveTarget.fieldName}
                key={saveTarget.token}
                onError={field.setError}
                token={saveTarget.token}
              />
            )
          }
          tester={field}
        >
          {field.resultNode}
        </PromptTestResultModal>
      )}
    </div>
  )
}

interface PromptTestButtonProps {
  className?: string
  field: PromptTester
}

// Runs the field's one tester, wherever the user happens to be standing when they ask.
export const PromptTestButton = ({
  className = "",
  field,
}: PromptTestButtonProps) => {
  const card = usePromptTestCardState(field)

  return (
    <Button
      className={`disabled:cursor-default ${className}`}
      disabled={card.runDisabled}
      onClick={() => void field.runTest()}
      variant="primary"
    >
      {field.isTesting ? (
        <LoaderCircle aria-hidden className="size-3.5 animate-spin" />
      ) : (
        <Play aria-hidden className="size-3.5 fill-current" />
      )}
      {field.isTesting ? "Testing…" : "Test"}
    </Button>
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
      variant="primary"
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
