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

import { ChevronLeft, ChevronRight, LoaderCircle, X } from "lucide-react"
import type { ReactNode } from "react"
import { useState } from "react"

import { Button } from "@/components/ui/Button"
import { Dialog, DialogTakeover, DialogTitle } from "@/components/ui/Dialog"
import { ErrorBanner } from "@/components/ui/ErrorBanner"
import { useVoiceCatalog } from "@/features/defaults/useVoiceCatalog"
import { useAppStore } from "@/store/appStore"
import type { AppState, SmartField } from "@/types/api"

import { hasSmartFieldCollision } from "./fieldEditor"
import type {
  FieldEditorDraft,
  FieldEditorMode,
  FieldEditorStep,
} from "./fieldEditor"
import { CompletionConfetti, StepDone } from "./StepDone"
import { StepPrompt } from "./StepPrompt"
import { StepTarget } from "./StepTarget"
import { useFieldEditor } from "./useFieldEditor"

export interface FieldEditorRequest {
  field?: SmartField
  initialNoteTypeId?: number
  mode: FieldEditorMode
  step?: FieldEditorStep
}

interface FieldEditorScreenProps extends FieldEditorRequest {
  onClose: () => void
  state: AppState
}

// Creating one is the magic moment, so only that title carries the sparkle.
const TITLES: Record<FieldEditorMode, string> = {
  create: "New Smart Field ✨",
  duplicate: "Duplicate Smart Field",
  edit: "Edit Smart Field",
}

export const FieldEditorScreen = ({
  field,
  initialNoteTypeId,
  mode,
  onClose,
  state,
  step,
}: FieldEditorScreenProps) => {
  const catalog = useAppStore((store) => store.catalog)
  const voiceCatalog = useVoiceCatalog()
  const [isOpen, setIsOpen] = useState(true)
  const close = () => setIsOpen(false)
  const controls = useFieldEditor({
    field,
    initialNoteTypeId,
    initialStep: step,
    mode,
    onClose: close,
    state,
  })
  const [hideCompletion, setHideCompletion] = useState(false)
  const collision = hasSmartFieldCollision(
    state.smartFields,
    controls.form.target,
    controls.form.editingFieldId,
  )
  const stepTwoInvalid =
    controls.form.isSaving ||
    (controls.form.target.fieldType === "tts"
      ? controls.form.sourceFieldName.trim() === ""
      : controls.form.prompt.trim() === "")
  const targetNoteTypeName =
    state.noteTypes.find(
      (noteType) => noteType.id === controls.form.target.noteTypeId,
    )?.name ?? ""

  return (
    <Dialog onOpenChange={setIsOpen} open={isOpen}>
      <DialogTakeover
        // No subtitle to point at, and a save in flight is not interruptible.
        aria-describedby={undefined}
        className="z-[60] bg-[#0d0d11]"
        data-testid="field-editor"
        onEscapeKeyDown={(event) => {
          if (controls.form.isSaving) event.preventDefault()
        }}
        // The editor stays up until its own exit animation lands; that is when the
        // screen behind can drop it. Animations inside it bubble here too.
        onAnimationEnd={(event) => {
          if (!isOpen && event.target === event.currentTarget) onClose()
        }}
      >
        {controls.form.step === 3 && <CompletionConfetti />}

        {/* One header contract for every step, shaped like a native titlebar and kept to a
          single row: dismiss or back as one icon button leading, title and target
          breadcrumb centered, sign-off trailing. */}
        {controls.form.step === 3 && (
          <DialogTitle className="sr-only">Smart Field created</DialogTitle>
        )}
        {controls.form.step !== 3 && (
          <header className="relative grid min-h-[52px] shrink-0 grid-cols-[1fr_auto_1fr] items-center gap-4 border-b border-white/[0.07] bg-black/10 px-4 py-2">
            <div className="flex min-w-0 items-center justify-start">
              {controls.form.step === 1 && (
                <HeaderIconButton label="Cancel" onClick={close}>
                  <X aria-hidden className="size-[18px]" />
                </HeaderIconButton>
              )}
              {controls.form.step === 2 && (
                <HeaderIconButton
                  label="Back"
                  onClick={() => controls.setStep(1)}
                >
                  <ChevronLeft aria-hidden className="size-[18px]" />
                </HeaderIconButton>
              )}
            </div>

            <div className="flex min-w-0 items-center justify-center gap-2.5">
              {/* Titlebar chrome, not content — it names the window and then gets out of
              the way, so it stays quieter than anything in the body. */}
              <DialogTitle asChild>
                <h1 className="shrink-0 text-[12.5px] leading-5 font-medium text-ink-muted">
                  {TITLES[mode]}
                </h1>
              </DialogTitle>
              {controls.form.step === 2 && (
                <>
                  <span
                    aria-hidden
                    className="h-3.5 w-px shrink-0 bg-white/15"
                  />
                  <TargetBreadcrumb form={controls.form} state={state} />
                </>
              )}
            </div>

            <div className="flex justify-end">
              {controls.form.step === 1 && (
                <Button
                  className="px-5"
                  disabled={
                    collision || controls.form.target.targetFieldName === ""
                  }
                  onClick={() => controls.setStep(2)}
                >
                  Next ›
                </Button>
              )}
              {controls.form.step === 2 && (
                <Button
                  className="px-5"
                  disabled={stepTwoInvalid || catalog === null}
                  variant="success"
                  onClick={() => void controls.save()}
                >
                  {controls.form.isSaving && (
                    <LoaderCircle
                      aria-hidden
                      className="size-3.5 animate-spin"
                    />
                  )}
                  {controls.form.isSaving ? "Saving…" : "Save Smart Field"}
                </Button>
              )}
            </div>
          </header>
        )}

        {controls.form.error !== null && (
          <ErrorBanner
            className="mx-6 mt-4 shrink-0"
            message={controls.form.error}
            onDismiss={controls.dismissError}
          />
        )}

        <div
          className={`relative min-h-0 flex-1 ${
            controls.form.step === 1
              ? "overflow-y-auto px-6 py-8"
              : controls.form.step === 2
                ? "overflow-y-auto px-6 py-6"
                : "overflow-y-auto px-6 py-8"
          }`}
        >
          {controls.form.step === 1 ? (
            <div className="mx-auto w-full max-w-[600px] pt-16">
              <StepTarget controls={controls} state={state} />
            </div>
          ) : controls.form.step === 3 ? (
            <div className="relative z-10 mx-auto w-full max-w-[800px] pt-[18px]">
              <StepDone
                noteTypeName={targetNoteTypeName}
                targetFieldName={controls.form.target.targetFieldName}
              />
            </div>
          ) : catalog === null ? (
            <div className="flex h-full min-h-56 items-center justify-center gap-2 text-xs text-ink-muted">
              <LoaderCircle aria-hidden className="size-4 animate-spin" />
              Loading model catalog…
            </div>
          ) : (
            <div className="mx-auto w-full max-w-[820px]">
              <div className="min-h-0">
                <StepPrompt
                  catalog={catalog}
                  controls={controls}
                  state={state}
                  voiceCatalog={voiceCatalog.catalog}
                />
              </div>
              {controls.form.target.fieldType === "tts" &&
                voiceCatalog.error !== null && (
                  <p className="mt-3 text-[11px] text-danger">
                    {voiceCatalog.error}
                  </p>
                )}
            </div>
          )}
        </div>

        {controls.form.step === 3 && (
          <footer className="relative z-10 flex shrink-0 items-center justify-between border-t border-white/[0.07] bg-black/20 px-5 py-2.5">
            <label className="flex cursor-pointer items-center gap-2 text-xs text-ink-muted select-none">
              <input
                checked={hideCompletion}
                className="m-0 size-3.5 cursor-pointer accent-indigo"
                onChange={(event) => {
                  setHideCompletion(event.target.checked)
                  if (event.target.checked)
                    void controls.setWizardCompletionHidden()
                }}
                type="checkbox"
              />
              Don’t show this again
            </label>
            <Button className="px-5" variant="success" onClick={close}>
              Done
            </Button>
          </footer>
        )}
      </DialogTakeover>
    </Dialog>
  )
}

const TYPE_EMOJI: Record<FieldEditorDraft["target"]["fieldType"], string> = {
  chat: "💬",
  image: "🖼️",
  tts: "🔈",
}

// The step-2 header identity, read as a path: the notes this binds to, then the field
// it fills. A breadcrumb reads as location — the earlier labeled chips read as a badge.
const TargetBreadcrumb = ({
  form,
  state,
}: {
  form: FieldEditorDraft
  state: AppState
}) => {
  const noteType = state.noteTypes.find(
    (item) => item.id === form.target.noteTypeId,
  )
  const deck = state.decks.find((item) => item.id === form.target.deckId)
  const showDeck =
    form.target.deckId !== state.globalDeckId && deck !== undefined

  return (
    <nav
      aria-label="Smart Field target"
      className="flex max-w-full min-w-0 items-center gap-1.5 text-[11.5px]"
    >
      <span className="max-w-[260px] truncate text-ink-muted">
        {noteType?.name ?? "…"}
      </span>
      {showDeck && (
        <>
          <span aria-hidden className="shrink-0 text-zinc-600">
            ·
          </span>
          <span className="max-w-[180px] truncate text-ink-muted">
            {deck.name}
          </span>
        </>
      )}
      <ChevronRight aria-hidden className="size-3 shrink-0 text-zinc-600" />
      <span aria-hidden className="shrink-0 text-[11px] leading-none">
        {TYPE_EMOJI[form.target.fieldType]}
      </span>
      <span className="truncate font-mono text-[11.5px] font-medium text-zinc-300">
        {form.target.targetFieldName}
      </span>
    </nav>
  )
}

// Header navigation reads as chrome, not as a form control: one icon button, always in
// the leading slot — ✕ to dismiss, ‹ to step back.
const HeaderIconButton = ({
  children,
  label,
  onClick,
}: {
  children: ReactNode
  label: string
  onClick: () => void
}) => (
  <button
    aria-label={label}
    className="-ml-1 inline-flex size-8 shrink-0 cursor-pointer items-center justify-center rounded-md text-zinc-400 transition hover:bg-white/[0.06] hover:text-zinc-100"
    onClick={onClick}
    title={label}
  >
    {children}
  </button>
)
