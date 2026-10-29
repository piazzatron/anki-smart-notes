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
import { useTranslation } from "react-i18next"

import { ValidPromptFields } from "@/components/shared/ValidPromptFields"
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
  const { t } = useTranslation()
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
        <div className="mb-2.5 flex min-h-[22px] items-center gap-4">
          <h2 className="text-[15px] leading-tight font-semibold text-zinc-100">
            {title}
          </h2>
          <RecentImagePills field={field} />
        </div>
      )}

      {!isResultVisible && field.error !== null && (
        <ErrorBanner
          className="mb-3"
          message={field.error}
          onDismiss={field.dismissError}
        />
      )}

      {field.fieldType === "tts" &&
        field.setPrompt !== null &&
        field.selectedNote !== null && (
          <div className="mb-3">
            <p className="mb-1.5 text-xs text-ink-muted">
              {t("promptTester.selectFieldToReadAloud")}
            </p>
            <div
              aria-label={t("promptTester.selectFieldToReadAloud")}
              className="flex flex-wrap gap-1.5"
              role="group"
            >
              {Object.keys(field.selectedNote.fields).map((fieldName) => {
                const isSelected = field.prompt === `{{${fieldName}}}`

                return (
                  <button
                    aria-pressed={isSelected}
                    className={`cursor-pointer rounded-full px-2.5 py-1.5 font-mono text-xs transition ${
                      isSelected
                        ? "bg-indigo text-white"
                        : "bg-zinc-800 text-zinc-300 hover:bg-zinc-700 hover:text-white"
                    }`}
                    key={fieldName}
                    onClick={() => field.setPrompt?.(`{{${fieldName}}}`)}
                    type="button"
                  >
                    {fieldName}
                  </button>
                )
              })}
            </div>
          </div>
        )}

      {/* Nothing above this tester owns the prompt, so it does. */}
      {field.fieldType !== "tts" && field.setPrompt !== null && (
        <div className="mb-3">
          <label
            className="mb-1.5 block text-xs text-ink-muted"
            htmlFor={promptFieldId}
          >
            {field.promptLabel}
          </label>
          <textarea
            className="min-h-16 w-full resize-y rounded-md bg-white/[0.05] px-3 py-2.5 font-mono text-[13px] leading-[1.55] text-zinc-200 transition outline-none placeholder:text-zinc-600 focus:bg-white/[0.07]"
            id={promptFieldId}
            onChange={(event) => field.setPrompt?.(event.target.value)}
            placeholder={t("promptTester.promptPlaceholder", {
              braces: "{{ double curly brackets }}",
            })}
            rows={2}
            value={field.prompt}
          />
          {field.selectedNote !== null && (
            <ValidPromptFields
              fieldNames={Object.keys(field.selectedNote.fields)}
            />
          )}
          {/* With no card picked, the prompt above runs on its own or against a card. */}
          {field.selectedNote === null && (
            <p className="mt-1.5 text-center text-xs text-ink-muted">
              {t("promptTester.or")}
            </p>
          )}
        </div>
      )}

      <div className="flex h-[54px] items-stretch gap-3">
        <div className="min-w-0 flex-1">
          <SelectedTestCard
            compact
            // Image testers reopen results from the numbered row below instead.
            compactAction={
              showResultModal &&
              field.fieldType !== "image" &&
              hasResult &&
              !isResultVisible ? (
                <button
                  className="shrink-0 cursor-pointer text-xs text-indigo-soft transition hover:text-indigo-soft/80"
                  onClick={() => setIsResultOpen(true)}
                >
                  {t("promptTester.viewResult")}
                </button>
              ) : undefined
            }
            deckName={card.deckName}
            missingFieldNames={card.missingFieldNames}
            note={field.selectedNote}
            noteTypeName={card.noteTypeName}
            referencedFields={card.referencedFields}
            requiredNoteTypeName={card.requiredNoteTypeName}
            selection={field.selection}
            showNoteTypeMismatch={field.hasNoteTypeMismatch}
          />
        </div>
        <PromptTestButton
          className="h-[54px] shrink-0 px-4 text-[13.5px]"
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
            saveTarget !== null ? (
              // Keyed by token: a new run mints a new one, and the previous save no
              // longer describes what is shown.
              <SaveResultButton
                cardId={saveTarget.cardId}
                fieldName={saveTarget.fieldName}
                key={saveTarget.token}
                onError={field.setError}
                token={saveTarget.token}
              />
            ) : saveTargetFieldName !== undefined && field.isEarlierRun ? (
              <p className="text-xs text-ink-muted">
                {t("promptTester.rerunToSave")}
              </p>
            ) : null
          }
          tester={field}
        >
          {field.resultNode}
        </PromptTestResultModal>
      )}
    </div>
  )
}

// Earlier image results stay a click away, numbered in the order they ran, so settings
// can be compared without re-running. Sits beside the tester's heading, wherever that is.
export const RecentImagePills = ({ field }: { field: PromptTester }) => {
  const { t } = useTranslation()
  if (field.imageHistory.length === 0) return null

  return (
    <div className="flex min-w-0 items-center gap-2">
      <div className="flex gap-1.5">
        {[...field.imageHistory].reverse().map((run, index) => (
          <button
            aria-label={t("promptTester.openRecentImage", {
              number: index + 1,
            })}
            className={`inline-flex h-[22px] min-w-[22px] items-center justify-center rounded-full px-1.5 text-[11.5px] leading-4 font-bold text-zinc-950 tabular-nums transition hover:scale-110 hover:brightness-110 ${RECENT_IMAGE_COLORS[index % RECENT_IMAGE_COLORS.length]}`}
            key={run.id}
            onClick={() => field.viewRun(run.id)}
            type="button"
          >
            {index + 1}
          </button>
        ))}
      </div>
      <p className="text-xs text-ink-muted">{t("promptTester.recentImages")}</p>
    </div>
  )
}

// A distinct pastel per recent image, so each reads as its own button.
const RECENT_IMAGE_COLORS = [
  "bg-pastel-sky",
  "bg-pastel-pink",
  "bg-pastel-mint",
  "bg-pastel-butter",
  "bg-pastel-lavender",
  "bg-pastel-peach",
]

interface PromptTestButtonProps {
  className?: string
  field: PromptTester
}

// Runs the field's tester.
const PromptTestButton = ({ className = "", field }: PromptTestButtonProps) => {
  const { t } = useTranslation()
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
      {field.isTesting ? t("promptTester.testing") : t("common.test")}
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
  const { t } = useTranslation()
  const [status, setStatus] = useState<"idle" | "saving" | "saved">("idle")

  const save = async () => {
    setStatus("saving")
    try {
      await saveTestResultToCard({ cardId, fieldName, token })
      setStatus("saved")
    } catch (error) {
      setStatus("idle")
      onError(errorMessage(error, t("promptTester.errors.saveResult")))
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
        ? t("promptTester.savedTo", { field: fieldName })
        : status === "saving"
          ? t("common.saving")
          : t("promptTester.saveToCard")}
    </Button>
  )
}
