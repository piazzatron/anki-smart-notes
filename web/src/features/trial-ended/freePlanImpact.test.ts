import { describe, expect, test } from "bun:test"

import type { ChatGenerationSettings, SmartField } from "@/types/api"

import { getFreePlanImpact } from "./freePlanImpact"

const AUTO_STANDARD: ChatGenerationSettings = {
  provider: "auto",
  model: "auto",
  reasoningLevel: "off",
  webSearchEnabled: false,
  stripHtml: true,
}

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

const voiceField = (enabled = true): SmartField => ({
  id: crypto.randomUUID(),
  noteTypeId: 1,
  deckId: 1,
  targetFieldName: "Audio",
  enabled,
  fieldType: "tts",
  settings: {
    sourceFieldName: "Front",
    provider: "google",
    model: "standard",
    voiceId: "en-US-Casual-K",
    usesDefaultGenerationSettings: true,
  },
})

describe("getFreePlanImpact", () => {
  test("counts enabled fields the free plan stops or downgrades", () => {
    const fields = [
      chatField({}),
      chatField({ reasoningLevel: "max" }),
      chatField({ provider: "openai", model: "gpt-5", webSearchEnabled: true }),
      chatField({ reasoningLevel: "high" }, false),
      voiceField(),
      voiceField(false),
    ]

    expect(getFreePlanImpact(fields, AUTO_STANDARD)).toEqual({
      voiceFields: 1,
      imageFields: 0,
      modelFallbacks: 2,
      webSearchFallbacks: 1,
    })
  })

  test("judges fields that follow the defaults by the defaults", () => {
    const fields = [chatField("default"), chatField("default")]

    expect(
      getFreePlanImpact(fields, { ...AUTO_STANDARD, reasoningLevel: "high" }),
    ).toMatchObject({ modelFallbacks: 2 })
    expect(getFreePlanImpact(fields, AUTO_STANDARD)).toMatchObject({
      modelFallbacks: 0,
    })
  })
})
