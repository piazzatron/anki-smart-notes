import { describe, expect, test } from "bun:test"

import type { VoiceCatalogItem } from "@/types/api"

import {
  filterVoices,
  previewTextForLanguage,
  voiceMatchesSettings,
} from "./voiceDefaults"

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
