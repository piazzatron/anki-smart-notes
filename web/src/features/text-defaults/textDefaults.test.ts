import { describe, expect, test } from "bun:test"

import type { SmartField } from "@/types/api"

import { getDefaultUsage } from "@/features/defaults/defaultUsage"

const textField = (
  id: string,
  usesDefaultGenerationSettings: boolean,
): SmartField => ({
  id,
  noteTypeId: 1,
  deckId: 1,
  targetFieldName: id,
  fieldType: "chat",
  enabled: true,
  settings: {
    promptText: "Define {{Front}}",
    provider: "auto",
    model: "auto",
    reasoningLevel: "off",
    webSearchEnabled: false,
    usesDefaultGenerationSettings,
  },
})

describe("Text Defaults", () => {
  test("counts fields following defaults separately from pinned fields", () => {
    expect(
      getDefaultUsage(
        [
          textField("one", true),
          textField("two", true),
          textField("three", false),
        ],
        "chat",
      ),
    ).toEqual({ following: 2, pinned: 1 })
  })
})
