import { describe, expect, test } from "bun:test"

import type {
  ChatGenerationSettings,
  SmartField,
  TTSGenerationSettings,
  VoiceCatalogItem,
  VoiceRule,
} from "@/types/api"

import { getFreePlanImpact } from "./freePlanImpact"

const AUTO_STANDARD: ChatGenerationSettings = {
  provider: "auto",
  model: "auto",
  reasoningLevel: "off",
  webSearchEnabled: false,
  stripHtml: true,
}

const CASUAL_K: TTSGenerationSettings = {
  provider: "google",
  model: "standard",
  voiceId: "en-US-Casual-K",
}

const FREE_VOICES: VoiceRule[] = [
  { provider: "google", model: "standard", voiceIdIncludes: "-Standard-" },
]

const catalogVoice = (
  settings: TTSGenerationSettings,
  language: string,
): VoiceCatalogItem => ({
  ...settings,
  name: settings.voiceId,
  gender: "Male",
  language,
  priceTier: "standard",
})

const VOICES = [
  catalogVoice(CASUAL_K, "English (United States)"),
  catalogVoice(
    { provider: "google", model: "standard", voiceId: "en-US-Standard-A" },
    "English (United States)",
  ),
  catalogVoice({ provider: "openai", model: "tts-1", voiceId: "onyx" }, "All"),
]

const chatField = (
  settings: Partial<ChatGenerationSettings> | "default",
  enabled = true,
): SmartField => ({
  id: crypto.randomUUID(),
  noteTypeId: 1,
  deckId: 1,
  targetFieldName: "Back",
  enabled,
  fieldType: "chat",
  settings: {
    ...AUTO_STANDARD,
    ...(settings === "default" ? {} : settings),
    promptText: "{{Front}}",
    usesDefaultGenerationSettings: settings === "default",
  },
})

const voiceField = (
  settings: TTSGenerationSettings | "default",
  enabled = true,
): SmartField => ({
  id: crypto.randomUUID(),
  noteTypeId: 1,
  deckId: 1,
  targetFieldName: "Audio",
  enabled,
  fieldType: "tts",
  settings: {
    ...(settings === "default" ? CASUAL_K : settings),
    sourceFieldName: "Front",
    usesDefaultGenerationSettings: settings === "default",
  },
})

const impactOf = (
  smartFields: SmartField[],
  chat: ChatGenerationSettings = AUTO_STANDARD,
) =>
  getFreePlanImpact({
    smartFields,
    defaults: { chat, tts: CASUAL_K },
    allowedVoices: FREE_VOICES,
    voices: VOICES,
  })

describe("getFreePlanImpact", () => {
  test("counts enabled fields the free plan stops or downgrades", () => {
    const fields = [
      chatField({}),
      chatField({ reasoningLevel: "max" }),
      chatField({ provider: "openai", model: "gpt-5", webSearchEnabled: true }),
      chatField({ reasoningLevel: "high" }, false),
      voiceField("default"),
      voiceField({ provider: "openai", model: "tts-1", voiceId: "onyx" }),
      voiceField({
        provider: "google",
        model: "standard",
        voiceId: "en-US-Standard-A",
      }),
      voiceField("default", false),
    ]

    expect(impactOf(fields)).toEqual({
      voiceStops: 0,
      voiceFallbacks: 2,
      imageFields: 0,
      modelFallbacks: 2,
      webSearchFallbacks: 1,
    })
  })

  test("judges fields that follow the defaults by the defaults", () => {
    const fields = [chatField("default"), chatField("default")]

    expect(
      impactOf(fields, { ...AUTO_STANDARD, reasoningLevel: "high" }),
    ).toMatchObject({ modelFallbacks: 2 })
    expect(impactOf(fields)).toMatchObject({ modelFallbacks: 0 })
  })
})
