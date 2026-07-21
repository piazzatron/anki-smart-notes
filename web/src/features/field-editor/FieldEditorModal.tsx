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

import { AlertCircle, LoaderCircle, X } from "lucide-react"
import { useEffect, useState } from "react"

import { Button } from "@/components/ui/Button"
import { useVoiceCatalog } from "@/features/voice-defaults/useVoiceCatalog"
import { useAppStore } from "@/store/appStore"
import type { AppState, SmartField } from "@/types/api"

import { hasSmartFieldCollision } from "./fieldEditor"
import type { FieldEditorMode, FieldEditorStep } from "./fieldEditor"
import { StepDone } from "./StepDone"
import { StepPrompt } from "./StepPrompt"
import { StepTarget } from "./StepTarget"
import { useFieldEditor } from "./useFieldEditor"

export interface FieldEditorRequest {
  field?: SmartField
  mode: FieldEditorMode
  step?: FieldEditorStep
}

interface FieldEditorModalProps extends FieldEditorRequest {
  onClose: () => void
  state: AppState
}

const TITLES: Record<FieldEditorMode, string> = {
  create: "Create Smart Field",
  duplicate: "Duplicate Smart Field",
  edit: "Edit Smart Field",
}

export const FieldEditorModal = ({
  field,
  mode,
  onClose,
  state,
  step,
}: FieldEditorModalProps) => {
  const catalog = useAppStore((store) => store.catalog)
  const voiceCatalog = useVoiceCatalog()
  const controls = useFieldEditor({
    field,
    initialStep: step,
    mode,
    onClose,
    state,
  })
  const [hideCompletion, setHideCompletion] = useState(false)
  const collision = hasSmartFieldCollision(
    state.smartFields,
    controls.form.target,
  )
  const stepTwoInvalid =
    controls.form.isSaving ||
    (controls.form.target.fieldType === "tts"
      ? controls.form.sourceFieldName.trim() === ""
      : controls.form.prompt.trim() === "")

  useEffect(() => {
    const closeOnEscape = (event: KeyboardEvent) => {
      if (event.key === "Escape") onClose()
    }
    window.addEventListener("keydown", closeOnEscape)
    return () => window.removeEventListener("keydown", closeOnEscape)
  }, [onClose])

  return (
    <div
      className="fixed inset-0 z-[70] flex items-center justify-center bg-black/60 p-5 backdrop-blur-[3px]"
      data-testid="field-editor-modal"
      onMouseDown={(event) => {
        if (event.target === event.currentTarget) onClose()
      }}
    >
      <div
        aria-labelledby="field-editor-title"
        aria-modal="true"
        className="flex max-h-[min(620px,calc(100vh-32px))] w-[664px] max-w-full flex-col overflow-hidden rounded-xl border border-white/[0.11] bg-panel-raised shadow-[0_28px_90px_rgba(0,0,0,0.72)]"
        onMouseDown={(event) => event.stopPropagation()}
        role="dialog"
      >
        <header className="flex shrink-0 items-center justify-between border-b border-white/[0.065] bg-white/[0.018] px-5 py-4">
          <h1
            className="text-[15px] font-bold tracking-[-0.01em] text-zinc-100"
            id="field-editor-title"
          >
            {TITLES[mode]}
          </h1>
          <button
            aria-label="Close Smart Field editor"
            className="inline-flex size-7 items-center justify-center rounded-md text-zinc-500 transition hover:bg-white/[0.06] hover:text-zinc-200"
            onClick={onClose}
          >
            <X aria-hidden className="size-4" />
          </button>
        </header>

        {controls.form.error !== null && (
          <div className="mx-5 mt-4 flex items-start gap-2 rounded-lg border border-red-300/15 bg-red-300/[0.06] px-3 py-2.5 text-xs text-danger">
            <AlertCircle aria-hidden className="mt-0.5 size-3.5 shrink-0" />
            <p className="min-w-0 flex-1">{controls.form.error}</p>
            <button aria-label="Dismiss error" onClick={controls.dismissError}>
              <X aria-hidden className="size-3.5" />
            </button>
          </div>
        )}

        <div className="min-h-0 flex-1 overflow-y-auto px-5 py-5">
          {controls.form.step === 1 ? (
            <StepTarget controls={controls} state={state} />
          ) : controls.form.step === 3 ? (
            <StepDone targetFieldName={controls.form.target.targetFieldName} />
          ) : catalog === null ? (
            <div className="flex min-h-56 items-center justify-center gap-2 text-xs text-ink-muted">
              <LoaderCircle aria-hidden className="size-4 animate-spin" />
              Loading model catalog…
            </div>
          ) : (
            <StepPrompt
              catalog={catalog}
              controls={controls}
              state={state}
              voiceCatalog={voiceCatalog.catalog}
            />
          )}
          {controls.form.step === 2 &&
            controls.form.target.fieldType === "tts" &&
            voiceCatalog.error !== null && (
              <p className="mt-3 text-[11px] text-danger">
                {voiceCatalog.error}
              </p>
            )}
        </div>

        <footer className="flex shrink-0 items-center justify-between gap-4 border-t border-white/[0.06] bg-black/20 px-5 py-3">
          {controls.form.step === 1 ? (
            <Button onClick={onClose}>Cancel</Button>
          ) : controls.form.step === 2 && mode !== "edit" ? (
            <Button onClick={() => controls.setStep(1)}>‹ Back</Button>
          ) : controls.form.step === 3 ? (
            <label className="flex cursor-pointer items-center gap-2 text-[11px] text-ink-muted">
              <input
                checked={hideCompletion}
                className="size-3.5 accent-emerald-400"
                onChange={(event) => {
                  setHideCompletion(event.target.checked)
                  if (event.target.checked)
                    void controls.setWizardCompletionHidden()
                }}
                type="checkbox"
              />
              Don&apos;t show this again
            </label>
          ) : (
            <span />
          )}

          {controls.form.step === 1 ? (
            <Button
              className="px-5"
              disabled={
                collision || controls.form.target.targetFieldName === ""
              }
              onClick={() => controls.setStep(2)}
            >
              Set Up Prompt ›
            </Button>
          ) : controls.form.step === 2 ? (
            <Button
              className="border-mint/50 bg-mint text-emerald-950 hover:border-mint hover:bg-mint/90"
              disabled={stepTwoInvalid || catalog === null}
              onClick={() => void controls.save()}
            >
              {controls.form.isSaving && (
                <LoaderCircle aria-hidden className="size-3.5 animate-spin" />
              )}
              {controls.form.isSaving
                ? "Saving…"
                : mode === "edit"
                  ? "Save Changes"
                  : "Create Field"}
            </Button>
          ) : (
            <Button
              className="border-mint/50 bg-mint text-emerald-950 hover:border-mint hover:bg-mint/90"
              onClick={onClose}
            >
              Done
            </Button>
          )}
        </footer>
      </div>
    </div>
  )
}
