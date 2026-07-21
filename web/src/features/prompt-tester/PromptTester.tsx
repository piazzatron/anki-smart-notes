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

import { modelLabel } from "@/lib/catalog"
import { testTextPrompt } from "@/services/commands"
import type { ChatGenerationSettings } from "@/types/api"

import { PromptTesterPanel, ResolvedPrompt } from "./PromptTesterPanel"
import { usePromptTester } from "./usePromptTester"

interface PromptTesterProps {
  hidePromptInput?: boolean
  prompt?: string
  settings: ChatGenerationSettings
}

export const PromptTester = ({
  hidePromptInput,
  prompt,
  settings,
}: PromptTesterProps) => {
  const tester = usePromptTester({
    fallbackError: "Could not test this prompt",
    initialPrompt: "Translate {{Expression}} into natural English.",
    prompt,
    run: ({ cardId, prompt }) => testTextPrompt({ cardId, prompt, settings }),
  })

  return (
    <PromptTesterPanel
      hidePromptInput={hidePromptInput}
      promptLabel="Prompt"
      runLabel={`Run with ${modelLabel(settings.model)}`}
      runningLabel="Running…"
      subtitle="Select a card in the Anki Browser, then run your prompt against it to test the selected model."
      tester={tester}
      textareaId="text-prompt-tester-prompt"
    >
      {tester.result !== null && tester.selectedNote !== null && (
        <div className="mt-[15px]">
          <p className="mb-2 text-[10px] font-semibold tracking-[0.05em] text-ink-faint uppercase">
            Result
          </p>
          <ResolvedPrompt
            note={tester.selectedNote}
            prompt={tester.result.prompt}
          />
          <p className="rounded-[7px] border border-white/[0.06] bg-white/[0.03] px-3 py-2.5 text-xs leading-[1.55] whitespace-pre-wrap text-zinc-200">
            {tester.result.value.text}
          </p>
          <p className="mt-[7px] text-[10.5px] text-ink-faint">
            {modelLabel(settings.model)} · {tester.result.latencyMs}ms
          </p>
        </div>
      )}
    </PromptTesterPanel>
  )
}
