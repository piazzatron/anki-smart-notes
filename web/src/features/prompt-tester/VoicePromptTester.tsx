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

import { testTTSPrompt } from "@/services/commands"
import type { TTSGenerationSettings } from "@/types/api"

import { AudioPlayer } from "./AudioPlayer"
import { ResolvedPrompt } from "./PromptTestResultModal"
import { PromptTesterStrip } from "./PromptTesterStrip"
import { usePromptTester } from "./usePromptTester"

interface VoicePromptTesterProps {
  prompt?: string
  requiredNoteTypeId?: number
  settings: TTSGenerationSettings
  // Only a tester bound to a Smart Field can write its result back to the card.
  targetFieldName?: string
  title: string
  voiceName: string
}

export const VoicePromptTester = ({
  prompt,
  requiredNoteTypeId,
  settings,
  targetFieldName,
  title,
  voiceName,
}: VoicePromptTesterProps) => {
  const tester = usePromptTester({
    fallbackError: "Could not generate audio",
    initialPrompt: "{{Expression}}",
    prompt,
    requiredNoteTypeId,
    run: ({ cardId, prompt }) =>
      testTTSPrompt({ cardId, settings, text: prompt }),
  })
  const result = tester.result !== null && tester.selectedNote !== null && (
    <>
      <ResolvedPrompt
        note={tester.selectedNote}
        prompt={tester.result.prompt}
      />
      <AudioPlayer
        autoPlay
        dataUrl={tester.result.value.dataUrl}
        label={voiceName}
      />
    </>
  )

  return (
    <PromptTesterStrip
      promptLabel="Text to speak"
      provenance={voiceName}
      saveTargetFieldName={targetFieldName}
      tester={tester}
      title={title}
    >
      {result}
    </PromptTesterStrip>
  )
}
