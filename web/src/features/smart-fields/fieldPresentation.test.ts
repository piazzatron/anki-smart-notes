import { describe, expect, test } from "bun:test"

import type { ChatSmartFieldSettings, SmartField } from "@/types/api"

import {
  smartFieldDescription,
  smartFieldModelLabel,
} from "./fieldPresentation"

const chatField = (settings: Partial<ChatSmartFieldSettings>): SmartField => ({
  id: "reading",
  noteTypeId: 1,
  deckId: 1,
  targetFieldName: "Reading",
  fieldType: "chat",
  enabled: true,
  settings: {
    promptText: "Generate {{Front}}",
    provider: "auto",
    model: "auto",
    reasoningLevel: "off",
    webSearchEnabled: false,
    usesDefaultGenerationSettings: false,
    stripHtml: true,
    ...settings,
  },
})

describe("Smart Field presentation", () => {
  test("on the free plan, paid-only text settings show as Auto Standard, followed or pinned", () => {
    const autoStandard = smartFieldModelLabel(chatField({}), false)

    for (const usesDefaultGenerationSettings of [true, false]) {
      const field = chatField({
        provider: "anthropic",
        model: "claude-sonnet-4-5",
        usesDefaultGenerationSettings,
      })
      expect(smartFieldModelLabel(field, true)).toBe(autoStandard)
      expect(smartFieldModelLabel(field, false)).not.toBe(autoStandard)
    }
  })

  test("describes TTS using its source field", () => {
    const field: SmartField = {
      id: "audio",
      noteTypeId: 1,
      deckId: 1,
      targetFieldName: "Audio",
      fieldType: "tts",
      enabled: true,
      settings: {
        sourceFieldName: "Front",
        provider: "google",
        model: "standard",
        voiceId: "en-US-Casual-K",
        usesDefaultGenerationSettings: false,
      },
    }

    expect(smartFieldDescription(field)).toBe("Reads {{Front}} aloud")
    expect(
      smartFieldModelLabel(field, false, [
        {
          provider: "google",
          model: "standard",
          voiceId: "en-US-Casual-K",
          name: "Casual K (Standard)",
          language: "English (United States)",
          gender: "Male",
          priceTier: "free",
        },
      ]),
    ).toBe("Google · Casual K (Standard)")
  })
})
