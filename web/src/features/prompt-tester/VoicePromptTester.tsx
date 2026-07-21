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
import { PromptTesterPanel, ResolvedPrompt } from "./PromptTesterPanel"
import { usePromptTester } from "./usePromptTester"

interface VoicePromptTesterProps {
  settings: TTSGenerationSettings
  voiceName: string
}

export const VoicePromptTester = ({
  settings,
  voiceName,
}: VoicePromptTesterProps) => {
  const tester = usePromptTester({
    fallbackError: "Could not generate audio",
    initialPrompt: "{{Expression}}",
    run: ({ cardId, prompt }) =>
      testTTSPrompt({ cardId, settings, text: prompt }),
  })

  return (
    <PromptTesterPanel
      promptLabel="Text to speak"
      runLabel={`Run with ${voiceName}`}
      runningLabel="Generating…"
      subtitle="Select a card in the Anki Browser, then hear the selected voice read it."
      tester={tester}
      textareaId="voice-prompt-tester-text"
    >
      {tester.result === null || tester.selectedNote === null ? (
        <div className="mt-[15px] rounded-lg border border-dashed border-white/[0.18] px-3 py-5 text-center text-[11px] text-ink-faint">
          Your generated audio appears here
        </div>
      ) : (
        <div className="mt-[15px]">
          <p className="mb-2 text-[10px] font-semibold tracking-[0.05em] text-ink-faint uppercase">
            Result
          </p>
          <ResolvedPrompt
            note={tester.selectedNote}
            prompt={tester.result.prompt}
          />
          <AudioPlayer
            autoPlay
            dataUrl={tester.result.value.dataUrl}
            label={voiceName}
          />
        </div>
      )}
    </PromptTesterPanel>
  )
}
