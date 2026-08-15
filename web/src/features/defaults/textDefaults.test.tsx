import { describe, expect, test } from "bun:test"
import { renderToStaticMarkup } from "react-dom/server"

import type { AppState, Catalog, SmartField } from "@/types/api"

import { DefaultUsagePill } from "./DefaultUsagePill"
import { getDefaultUsage } from "./defaultUsage"

const catalog: Catalog = {
  schemaVersion: 1,
  chat: {
    providers: ["auto", "openai"],
    models: [
      { id: "auto", provider: "auto" },
      { id: "gpt-5-mini", provider: "openai" },
    ],
    reasoningLevels: ["off", "low", "high"],
  },
  image: { providers: [], models: [] },
}

const state: AppState = {
  schemaVersion: 1,
  appVersion: "test",
  smartFields: [],
  noteTypes: [],
  decks: [],
  globalDeckId: 1,
  account: { status: "UNAUTHENTICATED", plan: null, email: null },
  featureFlags: { reviewFreeMonth: false },
  defaults: {
    chat: {
      provider: "auto",
      model: "auto",
      reasoningLevel: "off",
      webSearchEnabled: false,
    },
    image: { provider: "openai", model: "test" },
    tts: { provider: "openai", model: "test", voiceId: "test" },
  },
  settings: {
    debug: false,
    generateAtReview: true,
    legacyOpenAiHost: null,
    legacyOpenAiKey: null,
    legacyOpenAiModel: "gpt-5-mini",
    regenerateWhenBatching: false,
    showWizardCompletion: true,
    didDismissDiscordPrompt: false,
  },
}

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
  test("hides usage when no fields follow the default", () => {
    expect(
      renderToStaticMarkup(
        <DefaultUsagePill usage={{ following: 0, pinned: 1 }} />,
      ),
    ).toBe("")
  })

  test("does not include pinned fields in the usage label", () => {
    const markup = renderToStaticMarkup(
      <DefaultUsagePill usage={{ following: 2, pinned: 1 }} />,
    )

    expect(markup).toContain("Applies to 2 fields")
    expect(markup).not.toContain("pinned")
  })

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

  test("shows catalog-backed reasoning levels for Auto defaults", async () => {
    const markup = await renderTextDefaultsScreen(state)

    expect(markup).toContain('aria-label="Default reasoning level"')
    expect(markup).toContain('role="combobox"')
    expect(markup).toContain("Picking a model")
    expect(markup).toContain("Higher reasoning can improve harder generations")
    expect(markup.match(/Try it/g)).toHaveLength(1)
  })

  test("hides reasoning levels for models that do not support them", async () => {
    const markup = await renderTextDefaultsScreen({
      ...state,
      defaults: {
        ...state.defaults,
        chat: {
          ...state.defaults.chat,
          provider: "openai",
          model: "gpt-5-mini",
        },
      },
    })

    expect(markup).not.toContain('aria-label="Default reasoning level"')
  })
})

const renderTextDefaultsScreen = async (
  appState: AppState,
): Promise<string> => {
  Object.defineProperty(globalThis, "window", {
    configurable: true,
    value: { location: { search: "" } },
  })
  const { LoadedTextDefaultsScreen } = await import("./TextDefaultsScreen")

  return renderToStaticMarkup(
    <LoadedTextDefaultsScreen catalog={catalog} state={appState} />,
  )
}
