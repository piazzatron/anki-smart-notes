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
