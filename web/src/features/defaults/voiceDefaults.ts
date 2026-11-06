import type {
  AppState,
  TTSGenerationSettings,
  VoiceCatalogItem,
  VoiceRule,
} from "@/types/api"

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

/** The voices the signed-in plan allows, from the server, or null when it
 *  allows every voice. */
export const allowedVoicesOf = (state: AppState | null): VoiceRule[] | null =>
  state?.account.status === "AUTHENTICATED"
    ? (state.account.plan.allowedVoices ?? null)
    : null

/** Whether a plan with these voice rules can use a voice; null allows every
 *  voice. Mirrors the server's check. */
export const isVoiceAllowed = (
  voice: TTSGenerationSettings,
  rules: VoiceRule[] | null,
): boolean =>
  rules === null ||
  rules.some(
    (rule) =>
      rule.provider === voice.provider &&
      rule.model === voice.model &&
      voice.voiceId.includes(rule.voiceIdIncludes),
  )

/** A free voice reads in this language when the field's own language has none. */
const FALLBACK_LANGUAGE = "English (United States)"

/** The voice a plan with these rules generates with: this one when it's
 *  allowed, else an allowed voice in its language, or in US English when its
 *  language has none (OpenAI's voices have no single language), of its gender
 *  when there is one. Null when the plan allows neither. The plugin picks the
 *  same way (`plan_voice` in `voice_catalog.py`). */
export const planVoice = (
  settings: TTSGenerationSettings,
  voices: VoiceCatalogItem[],
  rules: VoiceRule[] | null,
): TTSGenerationSettings | null => {
  if (isVoiceAllowed(settings, rules)) return settings

  const current = voices.find((voice) => voiceMatchesSettings(voice, settings))
  const allowed = voices.filter((voice) => isVoiceAllowed(voice, rules))
  const inLanguage = allowed.filter(
    (voice) => voice.language === current?.language,
  )
  const candidates =
    inLanguage.length > 0
      ? inLanguage
      : allowed.filter((voice) => voice.language === FALLBACK_LANGUAGE)
  const match =
    candidates.find((voice) => voice.gender === current?.gender) ??
    candidates[0]
  return match === undefined
    ? null
    : { provider: match.provider, model: match.model, voiceId: match.voiceId }
}

/** What a picker shows for saved voice settings: the voice they read with on a
 *  plan with these rules, or the saved voice when there's none to stand in. The
 *  saved voice stays as it is for when the user upgrades. */
export const shownVoice = (
  settings: TTSGenerationSettings,
  voices: VoiceCatalogItem[],
  rules: VoiceRule[] | null,
): TTSGenerationSettings => planVoice(settings, voices, rules) ?? settings

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
