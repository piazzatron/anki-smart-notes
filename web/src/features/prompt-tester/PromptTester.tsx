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

import { ResolvedPrompt } from "./PromptTestResultModal"
import { PromptTesterStrip } from "./PromptTesterStrip"
import { usePromptTester } from "./usePromptTester"

interface PromptTesterProps {
  prompt?: string
  requiredNoteTypeId?: number
  settings: ChatGenerationSettings
  // Only a tester bound to a Smart Field can write its result back to the card.
  targetFieldName?: string
  title?: string
}

export const PromptTester = ({
  prompt,
  requiredNoteTypeId,
  settings,
  targetFieldName,
  title,
}: PromptTesterProps) => {
  const tester = usePromptTester({
    fallbackError: "Could not test this prompt",
    initialPrompt: "Translate {{Expression}} into natural English.",
    prompt,
    requiredNoteTypeId,
    run: ({ cardId, prompt }) =>
      testTextPrompt({ cardId: cardId!, prompt, settings }),
  })
  const result = tester.result !== null && tester.selectedNote !== null && (
    <>
      <ResolvedPrompt
        note={tester.selectedNote}
        prompt={tester.result.prompt}
      />
      <p className="text-[13px] leading-[1.6] whitespace-pre-wrap text-zinc-100">
        {tester.result.value.text}
      </p>
    </>
  )

  return (
    <PromptTesterStrip
      promptLabel="Prompt"
      provenance={modelLabel(settings.model)}
      saveTargetFieldName={targetFieldName}
      tester={tester}
      title={title}
    >
      {result}
    </PromptTesterStrip>
  )
}
