import { describe, expect, test } from "bun:test"

import type { AppState, SmartField } from "@/types/api"

import { getTextDefaultUsage, textDefaultsMatch } from "./textDefaults"

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
      getTextDefaultUsage([
        textField("one", true),
        textField("two", true),
        textField("three", false),
      ]),
    ).toEqual({ following: 2, pinned: 1 })
  })

  test("compares every persisted text setting", () => {
    const defaults: AppState["defaults"]["chat"] = {
      provider: "auto",
      model: "auto",
      reasoningLevel: "off",
      webSearchEnabled: false,
    }

    expect(textDefaultsMatch(defaults, { ...defaults })).toBe(true)
    expect(
      textDefaultsMatch(defaults, { ...defaults, webSearchEnabled: true }),
    ).toBe(false)
  })
})
