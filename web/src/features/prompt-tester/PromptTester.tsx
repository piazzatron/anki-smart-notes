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

import { AlertCircle, FileText, LoaderCircle, Sparkles, X } from "lucide-react"

import { hasGenerationAccess } from "@/components/shared/planPresentation"
import { Button } from "@/components/ui/Button"
import { modelLabel } from "@/lib/catalog"
import { useAppStore } from "@/store/appStore"
import type { ChatGenerationSettings } from "@/types/api"

import { usePromptTester } from "./usePromptTester"

interface PromptTesterProps {
  settings: ChatGenerationSettings
}

export const PromptTester = ({ settings }: PromptTesterProps) => {
  const account = useAppStore((store) => store.state?.account ?? null)
  const decks = useAppStore((store) => store.state?.decks ?? null)
  const tester = usePromptTester(settings)
  const selectedDeck = decks?.find(
    (deck) => deck.id === tester.selectedNote?.deckId,
  )
  const firstField =
    tester.selectedNote === null
      ? null
      : (Object.values(tester.selectedNote.fields)[0] ?? "(empty card)")

  return (
    <div>
      <p className="text-[10px] font-semibold tracking-[0.08em] text-ink-faint uppercase">
        Try it
      </p>

      {tester.error !== null && (
        <div className="mt-4 flex items-start gap-2 rounded-lg border border-red-300/15 bg-red-300/[0.06] px-3 py-2.5 text-xs text-danger">
          <AlertCircle aria-hidden className="mt-0.5 size-3.5 shrink-0" />
          <p className="min-w-0 flex-1">{tester.error}</p>
          <button aria-label="Dismiss error" onClick={tester.dismissError}>
            <X aria-hidden className="size-3.5" />
          </button>
        </div>
      )}

      <label
        className="mt-4 block text-[10.5px] font-medium text-zinc-400"
        htmlFor="text-prompt-tester-prompt"
      >
        Test prompt
      </label>
      <textarea
        className="mt-2 min-h-24 w-full resize-y rounded-lg border border-white/10 bg-white/[0.03] px-3 py-2.5 font-mono text-xs leading-5 text-zinc-200 transition outline-none placeholder:text-zinc-700 focus:border-indigo/45"
        id="text-prompt-tester-prompt"
        onChange={(event) => tester.setPrompt(event.target.value)}
        value={tester.prompt}
      />

      <div className="mt-4">
        {tester.selectedNote === null ? (
          <div className="flex items-center gap-3 rounded-lg border border-dashed border-white/[0.13] px-3 py-3">
            <FileText aria-hidden className="size-4 shrink-0 text-zinc-500" />
            <div>
              <p className="text-xs font-semibold text-zinc-300">
                Pick one card in the Anki Browser
              </p>
              <p className="mt-1 text-[10.5px] text-ink-muted">
                {tester.selection !== null &&
                tester.selection.note === null &&
                tester.selection.count > 1
                  ? `${tester.selection.count} cards selected — narrow it to one.`
                  : "Your selection appears here automatically."}
              </p>
            </div>
          </div>
        ) : (
          <div className="flex items-center gap-3">
            <div className="min-w-0 flex-1">
              <p className="truncate font-mono text-xs font-medium text-zinc-100">
                {firstField}
              </p>
              <p className="mt-1 truncate text-[10.5px] text-ink-faint">
                {selectedDeck?.name ?? "Selected card"}
              </p>
            </div>
            <span className="text-[10px] text-ink-faint">
              Change in Anki Browser
            </span>
            <Button
              disabled={
                account === null ||
                !hasGenerationAccess(account) ||
                tester.isTesting ||
                tester.prompt.trim() === ""
              }
              onClick={() => void tester.runTest()}
            >
              {tester.isTesting ? (
                <LoaderCircle aria-hidden className="size-3.5 animate-spin" />
              ) : (
                <Sparkles aria-hidden className="size-3.5" />
              )}
              {tester.isTesting
                ? "Running…"
                : tester.result === null
                  ? "Run"
                  : "Run again"}
            </Button>
          </div>
        )}
      </div>

      {tester.result !== null && (
        <PromptTestResult
          latencyMs={tester.result.latencyMs}
          model={tester.result.model}
          text={tester.result.text}
        />
      )}
    </div>
  )
}

interface PromptTestResultProps {
  latencyMs: number
  model: string
  text: string
}

const PromptTestResult = ({
  latencyMs,
  model,
  text,
}: PromptTestResultProps) => (
  <div className="mt-4 rounded-lg border border-white/[0.08] bg-white/[0.025] p-4">
    <div className="flex items-center gap-2 text-[10px] font-semibold tracking-[0.08em] text-indigo-soft uppercase">
      <Sparkles aria-hidden className="size-3.5" />
      Result
    </div>
    <p className="mt-3 text-[12.5px] leading-5 whitespace-pre-wrap text-zinc-200">
      {text}
    </p>
    <p className="mt-3 border-t border-white/[0.06] pt-2.5 text-[10px] text-ink-faint">
      {modelLabel(model)} · {latencyMs}ms · switch the model and run again to
      compare
    </p>
  </div>
)
