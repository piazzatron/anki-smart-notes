import type { TTSGenerationSettings, VoiceCatalogItem } from "@/types/api"

const DEFAULT_PREVIEW_TEXT =
  "This is a preview of your selected Smart Notes voice."

const PREVIEW_TEXTS: Record<string, string> = {
  Japanese: "こんにちは、今日はいい天気ですね。",
}

export const previewTextForLanguage = (language: string): string =>
  PREVIEW_TEXTS[language] ?? DEFAULT_PREVIEW_TEXT

export const voiceKey = (voice: VoiceCatalogItem): string =>
  `${voice.provider}:${voice.model}:${voice.voiceId}`

export const voiceMatchesSettings = (
  voice: VoiceCatalogItem,
  settings: TTSGenerationSettings,
): boolean =>
  voice.provider === settings.provider &&
  voice.model === settings.model &&
  voice.voiceId === settings.voiceId

export const filterVoices = (
  voices: VoiceCatalogItem[],
  filters: {
    gender: string
    language: string
    provider: string
    search: string
  },
): VoiceCatalogItem[] => {
  const searchTerms = filters.search
    .toLowerCase()
    .trim()
    .split(/\s+/)
    .filter(Boolean)
  return voices.filter((voice) => {
    if (filters.provider !== "All" && voice.provider !== filters.provider)
      return false
    if (filters.gender !== "All" && voice.gender !== filters.gender)
      return false
    if (
      filters.language !== "All" &&
      voice.language !== "All" &&
      voice.language !== filters.language
    )
      return false

    const haystack =
      `${voice.name} ${voice.provider} ${voice.language} ${voice.gender} ${voice.model}`.toLowerCase()
    return searchTerms.every((term) => haystack.includes(term))
  })
}
