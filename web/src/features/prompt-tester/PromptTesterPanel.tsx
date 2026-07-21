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

import { AlertCircle, LoaderCircle, Play, X } from "lucide-react"
import type { ReactNode } from "react"

import { hasGenerationAccess } from "@/components/shared/planPresentation"
import { Button } from "@/components/ui/Button"
import { useAppStore } from "@/store/appStore"
import type { SelectedNote } from "@/types/api"

import { SelectedTestCard } from "./SelectedTestCard"
import type { PromptTesterControls } from "./usePromptTester"

export const FIELD_REFERENCE_PATTERN = /\{\{([^{}]+)\}\}/g

interface PromptTesterPanelProps<R> {
  children: ReactNode
  promptLabel: string
  runLabel: string
  runningLabel: string
  subtitle: string
  tester: PromptTesterControls<R>
  textareaId: string
}

export const PromptTesterPanel = <R,>({
  children,
  promptLabel,
  runLabel,
  runningLabel,
  subtitle,
  tester,
  textareaId,
}: PromptTesterPanelProps<R>) => {
  const account = useAppStore((store) => store.state?.account ?? null)
  const decks = useAppStore((store) => store.state?.decks ?? null)
  const noteTypes = useAppStore((store) => store.state?.noteTypes ?? null)
  const selectedDeck = decks?.find(
    (deck) => deck.id === tester.selectedNote?.deckId,
  )
  const selectedNoteType = noteTypes?.find(
    (noteType) => noteType.id === tester.selectedNote?.noteTypeId,
  )
  const referencedFieldNames = new Set(
    [...tester.prompt.matchAll(FIELD_REFERENCE_PATTERN)].map(
      (match) => match[1]!,
    ),
  )
  const runDisabled =
    tester.selectedNote === null ||
    account === null ||
    !hasGenerationAccess(account) ||
    tester.isTesting ||
    tester.prompt.trim() === ""

  return (
    <div className="rounded-[10px] border border-white/[0.09] bg-white/[0.02] px-4 pt-4 pb-[18px]">
      <h2 className="text-[15px] font-bold text-ink">Try it</h2>
      <p className="mt-1 mb-[13px] text-[11.5px] leading-[1.5] text-ink-muted">
        {subtitle}
      </p>

      {tester.error !== null && (
        <div className="mb-4 flex items-start gap-2 rounded-lg border border-red-300/15 bg-red-300/[0.06] px-3 py-2.5 text-xs text-danger">
          <AlertCircle aria-hidden className="mt-0.5 size-3.5 shrink-0" />
          <p className="min-w-0 flex-1">{tester.error}</p>
          <button
            aria-label="Dismiss error"
            className="cursor-pointer"
            onClick={tester.dismissError}
          >
            <X aria-hidden className="size-3.5" />
          </button>
        </div>
      )}

      <p className="mb-2 text-[10px] font-semibold tracking-[0.05em] text-ink-faint uppercase">
        Test card
      </p>
      <SelectedTestCard
        deckName={selectedDeck?.name ?? "Selected deck"}
        note={tester.selectedNote}
        noteTypeName={selectedNoteType?.name ?? "Selected note type"}
        referencedFieldNames={referencedFieldNames}
        selection={tester.selection}
      />

      <label
        className="mt-4 mb-2 block text-[10px] font-semibold tracking-[0.05em] text-ink-faint uppercase"
        htmlFor={textareaId}
      >
        {promptLabel}
      </label>
      <textarea
        className="min-h-20 w-full resize-y rounded-[7px] border border-white/10 bg-white/[0.03] px-[11px] py-[9px] font-mono text-xs leading-[1.55] text-zinc-200 transition outline-none placeholder:text-zinc-700 focus:border-indigo/45"
        id={textareaId}
        onChange={(event) => tester.setPrompt(event.target.value)}
        value={tester.prompt}
      />

      <Button
        className="mt-3 w-full py-2 text-[12.5px] disabled:cursor-default disabled:opacity-35"
        disabled={runDisabled}
        onClick={() => void tester.runTest()}
        variant="primary"
      >
        {tester.isTesting ? (
          <LoaderCircle aria-hidden className="size-3.5 animate-spin" />
        ) : (
          <Play aria-hidden className="size-3.5 fill-current" />
        )}
        {tester.isTesting ? runningLabel : runLabel}
      </Button>

      {children}
    </div>
  )
}

interface ResolvedPromptProps {
  note: SelectedNote
  prompt: string
}

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
