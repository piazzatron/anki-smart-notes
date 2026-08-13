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

import { useEffect } from "react"

import { testTTSPrompt } from "@/services/commands"
import type {
  MediaPreviewResult,
  MediaTestResult,
  TTSGenerationSettings,
} from "@/types/api"

import { PromptTesterStrip } from "./PromptTesterStrip"
import { usePromptTester } from "./usePromptTester"

interface VoicePromptTesterProps {
  prompt?: string
  requiredNoteTypeId?: number
  settings: TTSGenerationSettings
  title?: string
  voiceName: string
}

export const VoicePromptTester = ({
  prompt,
  requiredNoteTypeId,
  settings,
  title,
  voiceName,
}: VoicePromptTesterProps) => {
  const canRunWithoutCard = prompt === undefined
  const tester = usePromptTester<MediaTestResult | MediaPreviewResult>({
    canRunWithoutCard,
    fallbackError: "Could not generate audio",
    initialPrompt: "This is an example of your selected Smart Notes voice.",
    prompt,
    requiredNoteTypeId,
    run: ({ cardId, prompt }) =>
      testTTSPrompt({ cardId: cardId ?? undefined, settings, text: prompt }),
  })
  const resultValue = tester.result?.value

  useEffect(() => {
    if (resultValue === undefined) return

    const audio = new Audio(resultValue.dataUrl)
    void audio.play()
    return () => audio.pause()
  }, [resultValue])

  return (
    <PromptTesterStrip
      promptLabel="Text to speak"
      provenance={voiceName}
      showResultModal={false}
      tester={tester}
      title={title}
    />
  )
}
