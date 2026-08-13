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

import { useState } from "react"

import { modelLabel } from "@/lib/catalog"
import { testImagePrompt } from "@/services/commands"
import type { ImageGenerationSettings } from "@/types/api"

import { ResolvedPrompt } from "./PromptTestResultModal"
import { PromptTesterStrip } from "./PromptTesterStrip"
import { usePromptTester } from "./usePromptTester"

interface ImagePromptTesterProps {
  prompt?: string
  requiredNoteTypeId?: number
  settings: ImageGenerationSettings
  // Only a tester bound to a Smart Field can write its result back to the card.
  targetFieldName?: string
  title?: string
}

export const ImagePromptTester = ({
  prompt,
  requiredNoteTypeId,
  settings,
  targetFieldName,
  title,
}: ImagePromptTesterProps) => {
  const [dimensions, setDimensions] = useState<{
    height: number
    width: number
  } | null>(null)
  const tester = usePromptTester({
    fallbackError: "Could not generate an image",
    initialPrompt: "A memorable scene illustrating {{Expression}}.",
    prompt,
    requiredNoteTypeId,
    run: async ({ cardId, prompt }) => {
      const result = await testImagePrompt({ cardId: cardId!, prompt, settings })
      setDimensions(null)
      return result
    },
  })
  const result = tester.result !== null && tester.selectedNote !== null && (
    <>
      <ResolvedPrompt
        note={tester.selectedNote}
        prompt={tester.result.prompt}
      />
      <img
        alt="Generated image preview"
        className="max-h-[50vh] w-full rounded-lg border border-white/[0.1] bg-black/20 object-contain"
        onLoad={(event) =>
          setDimensions({
            height: event.currentTarget.naturalHeight,
            width: event.currentTarget.naturalWidth,
          })
        }
        src={tester.result.value.dataUrl}
      />
      {dimensions !== null && (
        <p className="mt-2 text-right text-[10.5px] text-ink-faint">
          {dimensions.width} × {dimensions.height}
        </p>
      )}
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
