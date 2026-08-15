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

import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogTitle,
} from "@/components/ui/Dialog"
import { ErrorBanner } from "@/components/ui/ErrorBanner"
import type { SelectedNote } from "@/types/api"

import { FIELD_REFERENCE_PATTERN } from "./promptTestCard"
import type { PromptTester } from "./usePromptTester"

interface PromptTestResultModalProps {
  children: ReactNode
  onClose: () => void
  open: boolean
  provenance: string
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
  const firstFieldValue = Object.values(
    tester.selectedNote?.fields ?? {},
  )[0]?.trim()
  const subtitle =
    tester.selectedNote === null
      ? provenance
      : [
          firstFieldValue === undefined || firstFieldValue === ""
            ? "Selected card"
            : firstFieldValue,
          provenance,
        ].join(" · ")

  return (
    <Dialog
      onOpenChange={(isOpen) => {
        if (!isOpen) onClose()
      }}
      open={open}
    >
      <DialogContent className="max-h-[84vh] w-[min(760px,92vw)]">
        <header className="shrink-0 border-b border-white/[0.07] py-3.5 pr-10 pl-5">
          <DialogTitle className="text-[13px] font-bold text-ink">
            Test result
          </DialogTitle>
          <DialogDescription className="mt-0.5 truncate text-[11px] text-ink-faint">
            {subtitle}
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
  note: SelectedNote
  prompt: string
}

/** The prompt as it was actually sent: field references swapped for the card's text. */
export const ResolvedPrompt = ({ note, prompt }: ResolvedPromptProps) => {
  const fragments: ReactNode[] = []
  let previousEnd = 0

  for (const match of prompt.matchAll(FIELD_REFERENCE_PATTERN)) {
    const matchIndex = match.index
    if (matchIndex > previousEnd) {
      fragments.push(prompt.slice(previousEnd, matchIndex))
    }
    fragments.push(
      <span className="text-indigo-soft" key={`${matchIndex}-${match[0]}`}>
        {note.fields[match[1]!] ?? match[0]}
      </span>,
    )
    previousEnd = matchIndex + match[0].length
  }
  if (previousEnd < prompt.length) fragments.push(prompt.slice(previousEnd))

  return (
    <p className="mb-2 font-mono text-[11px] leading-[1.5] text-ink-muted">
      <span className="font-sans text-[10.5px] text-ink-faint">Sent · </span>
      {fragments}
    </p>
  )
}
