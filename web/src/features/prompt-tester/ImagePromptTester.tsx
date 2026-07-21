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

import { PromptTesterPanel, ResolvedPrompt } from "./PromptTesterPanel"
import { usePromptTester } from "./usePromptTester"

interface ImagePromptTesterProps {
  hidePromptInput?: boolean
  prompt?: string
  settings: ImageGenerationSettings
}

export const ImagePromptTester = ({
  hidePromptInput,
  prompt,
  settings,
}: ImagePromptTesterProps) => {
  const [dimensions, setDimensions] = useState<{
    height: number
    width: number
  } | null>(null)
  const [isExpanded, setIsExpanded] = useState(false)
  const tester = usePromptTester({
    fallbackError: "Could not generate an image",
    initialPrompt: "A memorable scene illustrating {{Expression}}.",
    prompt,
    run: async ({ cardId, prompt }) => {
      const result = await testImagePrompt({ cardId, prompt, settings })
      setDimensions(null)
      return result
    },
  })

  return (
    <PromptTesterPanel
      hidePromptInput={hidePromptInput}
      promptLabel="Prompt"
      runLabel={`Run with ${modelLabel(settings.model)}`}
      runningLabel="Running…"
      subtitle="Select a card in the Anki Browser, then run your prompt against it to test the selected model."
      tester={tester}
      textareaId="image-prompt-tester-prompt"
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
          <button
            aria-label="Enlarge generated image"
            className="block w-full cursor-pointer overflow-hidden rounded-lg border border-white/[0.1] bg-black/20"
            onClick={() => setIsExpanded(true)}
          >
            <img
              alt="Generated image preview"
              className="max-h-72 w-full object-contain"
              onLoad={(event) =>
                setDimensions({
                  height: event.currentTarget.naturalHeight,
                  width: event.currentTarget.naturalWidth,
                })
              }
              src={tester.result.value.dataUrl}
            />
          </button>
          {dimensions !== null && (
            <p className="mt-[7px] text-right text-[10.5px] text-ink-faint">
              {dimensions.width} × {dimensions.height} · click to enlarge
            </p>
          )}
        </div>
      )}

      {isExpanded && tester.result !== null && (
        <button
          aria-label="Close enlarged image"
          className="fixed inset-0 z-[80] flex cursor-zoom-out items-center justify-center bg-black/85 p-8"
          onClick={() => setIsExpanded(false)}
        >
          <img
            alt="Generated image preview enlarged"
            className="max-h-full max-w-full rounded-lg object-contain shadow-2xl"
            src={tester.result.value.dataUrl}
          />
        </button>
      )}
    </PromptTesterPanel>
  )
}
