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

import type { ReactNode } from "react"
import { useTranslation } from "react-i18next"

import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogTitle,
} from "@/components/ui/Dialog"
import { ErrorBanner } from "@/components/ui/ErrorBanner"
import { Pill } from "@/components/ui/Pill"
import type { SelectedNote } from "@/types/api"

import { resolvePromptReferences } from "./resolvePromptReferences"
import type { PromptTester, Provenance } from "./usePromptTester"

interface PromptTestResultModalProps {
  children: ReactNode
  onClose: () => void
  open: boolean
  provenance: Provenance | null
  saveAction?: ReactNode
  tester: PromptTester
}

// Every tester presents its result through this dialog. The surrounding panel or
// strip owns how a test is configured; this component owns result presentation.
export const PromptTestResultModal = ({
  children,
  onClose,
  open,
  provenance,
  saveAction = null,
  tester,
}: PromptTestResultModalProps) => {
  const { t } = useTranslation()
  const firstFieldValue = Object.values(
    tester.selectedNote?.fields ?? {},
  )[0]?.trim()
  const cardName =
    tester.selectedNote === null
      ? null
      : firstFieldValue === undefined || firstFieldValue === ""
        ? t("promptTester.selectedCard")
        : firstFieldValue

  return (
    <Dialog
      onOpenChange={(isOpen) => {
        if (!isOpen) onClose()
      }}
      open={open}
    >
      {/* An image result gets a narrower dialog that hugs the picture; text needs the
          room to read. */}
      <DialogContent
        className={`max-h-[84vh] ${tester.fieldType === "image" ? "w-[min(520px,92vw)]" : "w-[min(760px,92vw)]"}`}
      >
        <header className="shrink-0 border-b border-white/[0.07] py-3.5 ps-5 pe-10">
          <DialogTitle className="text-[13px] font-bold text-ink">
            {t("promptTester.testResult")}
          </DialogTitle>
          <DialogDescription className="mt-1.5 flex min-w-0 items-center gap-1.5 text-[11px] text-ink-faint">
            {cardName !== null && (
              <span className="min-w-0 truncate">{cardName} ·</span>
            )}
            {provenance !== null && (
              <>
                <Pill>{provenance.primary}</Pill>
                {provenance.extras.map((extra) => (
                  <Pill key={extra} tone="indigo">
                    {extra}
                  </Pill>
                ))}
              </>
            )}
          </DialogDescription>
        </header>

        <div className="min-h-0 flex-1 overflow-y-auto px-5 py-4">
          {tester.error !== null && (
            <ErrorBanner
              className="mb-3"
              message={tester.error}
              onDismiss={tester.dismissError}
            />
          )}
          {children}
        </div>

        {saveAction !== null && (
          <footer className="flex shrink-0 items-center justify-end border-t border-white/[0.07] px-5 py-3">
            {saveAction}
          </footer>
        )}
      </DialogContent>
    </Dialog>
  )
}

interface ResolvedPromptProps {
  note: SelectedNote | null
  prompt: string
}

/** The prompt as it was actually sent: field references swapped for the card's text. */
export const ResolvedPrompt = ({ note, prompt }: ResolvedPromptProps) => {
  const { t } = useTranslation()
  const { parts } = resolvePromptReferences(prompt, note?.fields ?? {})

  return (
    <p className="mb-2 font-mono text-[11px] leading-[1.5] text-ink-muted">
      <span className="font-sans text-[10.5px] text-ink-faint">
        {t("promptTester.sent")} ·{" "}
      </span>
      {parts.map((part, index) =>
        part.isReference ? (
          <span className="text-indigo-soft" key={index}>
            {part.text}
          </span>
        ) : (
          part.text
        ),
      )}
    </p>
  )
}
