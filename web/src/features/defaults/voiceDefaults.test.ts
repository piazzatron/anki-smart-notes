import { describe, expect, test } from "bun:test"

import type {
  TTSGenerationSettings,
  VoiceCatalogItem,
  VoiceRule,
} from "@/types/api"

import {
  filterVoices,
  planVoice,
  previewTextForLanguage,
  voiceMatchesSettings,
} from "./voiceDefaults"

// What the server sends as the free plan's voices.
const FREE_VOICES: VoiceRule[] = [
  { provider: "google", model: "standard", voiceIdIncludes: "-Standard-" },
]

const voiceSettings = (
  provider: string,
  model: string,
  voiceId: string,
): TTSGenerationSettings => ({ provider, model, voiceId })

const catalogVoice = (
  settings: TTSGenerationSettings,
  language: string,
  gender: VoiceCatalogItem["gender"],
): VoiceCatalogItem => ({
  ...settings,
  name: settings.voiceId,
  gender,
  language,
  priceTier: "standard",
})

const planVoices: VoiceCatalogItem[] = [
  catalogVoice(
    voiceSettings("google", "neural", "ja-JP-Neural2-B"),
    "Japanese",
    "Female",
  ),
  catalogVoice(
    voiceSettings("google", "standard", "ja-JP-Standard-C"),
    "Japanese",
    "Male",
  ),
  catalogVoice(
    voiceSettings("google", "standard", "ja-JP-Standard-A"),
    "Japanese",
    "Female",
  ),
  catalogVoice(
    voiceSettings("voicevox", "voicevox", "3"),
    "Japanese",
    "Female",
  ),
  catalogVoice(
    voiceSettings("google", "standard", "en-US-Casual-K"),
    "English (United States)",
    "Male",
  ),
  catalogVoice(
    voiceSettings("google", "standard", "en-US-Standard-C"),
    "English (United States)",
    "Female",
  ),
  catalogVoice(
    voiceSettings("openai", "gpt-4o-mini-tts", "coral"),
    "All",
    "Female",
  ),
]

const voices: VoiceCatalogItem[] = [
  {
    provider: "google",
    voiceId: "ja-JP-Neural2-B",
    model: "neural",
    name: "Japanese Female (Neural)",
    gender: "Female",
    language: "Japanese",
    priceTier: "standard",
  },
  {
    provider: "openai",
    voiceId: "coral",
    model: "gpt-4o-mini-tts",
    name: "Coral (4o-mini)",
    gender: "Female",
    language: "All",
    priceTier: "standard",
  },
  {
    provider: "google",
    voiceId: "en-US-Standard-A",
    model: "standard",
    name: "English Male (Standard)",
    gender: "Male",
    language: "English",
    priceTier: "low",
  },
]

describe("Voice Defaults", () => {
  test("combines language, gender, provider, and search filters", () => {
    expect(
      filterVoices(voices, {
        gender: "Female",
        language: "Japanese",
        provider: "google",
        search: "neural",
      }),
    ).toEqual([voices[0]])
  })

  test("multilingual voices remain visible for a specific language", () => {
    expect(
      filterVoices(voices, {
        gender: "All",
        language: "Japanese",
        provider: "All",
        search: "",
      }),
    ).toEqual([voices[0], voices[1]])
  })

  test("matches all three persisted voice identifiers", () => {
    expect(
      voiceMatchesSettings(voices[1]!, {
        provider: "openai",
        model: "gpt-4o-mini-tts",
        voiceId: "coral",
      }),
    ).toBe(true)
    expect(
      voiceMatchesSettings(voices[1]!, {
        provider: "openai",
        model: "tts-1",
        voiceId: "coral",
      }),
    ).toBe(false)
  })

  test.each<{
    name: string
    saved: TTSGenerationSettings
    rules: VoiceRule[] | null
    expected: string | null
  }>([
    {
      name: "paid plans keep any voice",
      saved: voiceSettings("voicevox", "voicevox", "3"),
      rules: null,
      expected: "3",
    },
    {
      name: "a free voice is kept",
      saved: voiceSettings("google", "standard", "ja-JP-Standard-C"),
      rules: FREE_VOICES,
      expected: "ja-JP-Standard-C",
    },
    {
      name: "another voice uses a free one in its language and gender",
      saved: voiceSettings("google", "neural", "ja-JP-Neural2-B"),
      rules: FREE_VOICES,
      expected: "ja-JP-Standard-A",
    },
    {
      name: "a Premium voice filed under Standard isn't free",
      saved: voiceSettings("google", "standard", "en-US-Casual-K"),
      rules: FREE_VOICES,
      expected: "en-US-Standard-C",
    },
    {
      name: "a voice with no free one in its language reads in US English",
      saved: voiceSettings("openai", "gpt-4o-mini-tts", "coral"),
      rules: FREE_VOICES,
      expected: "en-US-Standard-C",
    },
  ])("planVoice: $name", ({ saved, rules, expected }) => {
    expect(planVoice(saved, planVoices, rules)?.voiceId ?? null).toBe(expected)
  })

  test("uses the language-specific voice preview text", () => {
    expect(previewTextForLanguage("Japanese")).toBe(
      "こんにちは、今日はいい天気ですね。",
    )
  })

  test("uses the English voice preview text for unmapped languages", () => {
    expect(previewTextForLanguage("French")).toBe(
      "This is a preview of your selected Smart Notes voice.",
    )
  })
})
