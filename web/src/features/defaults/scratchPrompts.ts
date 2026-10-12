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

import { useCallback } from "react"
import { create } from "zustand"

type ScratchPromptScreen = "image" | "text"

const useScratchPromptStore = create<{
  prompts: Partial<Record<ScratchPromptScreen, string>>
}>(() => ({ prompts: {} }))

/** The prompt typed into a defaults screen's tester. It lives outside the screen so it
 *  survives switching screens for as long as the window stays open. */
export const useScratchPrompt = (
  screen: ScratchPromptScreen,
  samplePrompt: string,
): [string, (prompt: string) => void] => {
  const prompt =
    useScratchPromptStore((store) => store.prompts[screen]) ?? samplePrompt
  const setPrompt = useCallback(
    (next: string) =>
      useScratchPromptStore.setState((store) => ({
        prompts: { ...store.prompts, [screen]: next },
      })),
    [screen],
  )

  return [prompt, setPrompt]
}
