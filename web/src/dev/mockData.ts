import { useAppStore } from "@/store/appStore"
import type { SmartField } from "@/features/smart-fields/types"
import type { AppState, Catalog } from "@/store/appStore"

const GLOBAL_DECK_ID = 1

const POPULATED_FIELDS: SmartField[] = [
  {
    id: "reading",
    noteTypeId: 100,
    deckId: GLOBAL_DECK_ID,
    targetFieldName: "Reading",
    fieldType: "chat",
    enabled: true,
    settings: {
      promptText:
        "Generate furigana for {{Expression}}. Return only the reading.",
      provider: "auto",
      model: "auto",
      reasoningLevel: "off",
      webSearchEnabled: false,
      usesDefaultGenerationSettings: true,
    },
  },
  {
    id: "meaning",
    noteTypeId: 100,
    deckId: GLOBAL_DECK_ID,
    targetFieldName: "Meaning",
    fieldType: "chat",
    enabled: true,
    settings: {
      promptText:
        "Translate {{Expression}} into natural English. Return only the translation.",
      provider: "auto",
      model: "auto",
      reasoningLevel: "off",
      webSearchEnabled: false,
      usesDefaultGenerationSettings: true,
    },
  },
  {
    id: "image",
    noteTypeId: 100,
    deckId: GLOBAL_DECK_ID,
    targetFieldName: "Image",
    fieldType: "image",
    enabled: true,
    settings: {
      promptText: "A memorable scene illustrating {{Expression}}.",
      provider: "openai",
      model: "gpt-image-1.5-low",
      usesDefaultGenerationSettings: false,
    },
  },
  {
    id: "audio-off",
    noteTypeId: 200,
    deckId: GLOBAL_DECK_ID,
    targetFieldName: "JP_Audio",
    fieldType: "tts",
    enabled: false,
    settings: {
      sourceFieldName: "Front",
      provider: "google",
      model: "standard",
      voiceId: "en-US-Casual-K",
      usesDefaultGenerationSettings: true,
    },
  },
  {
    id: "deck-audio",
    noteTypeId: 100,
    deckId: 20,
    targetFieldName: "Example_TTS",
    fieldType: "tts",
    enabled: true,
    settings: {
      sourceFieldName: "Example",
      provider: "elevenLabs",
      model: "eleven_multilingual_v2",
      voiceId: "Rachel",
      usesDefaultGenerationSettings: false,
    },
  },
]

const BASE_STATE: AppState = {
  schemaVersion: 1,
  smartFields: POPULATED_FIELDS,
  noteTypes: [
    {
      id: 100,
      name: "Japanese",
      fields: [
        "Expression",
        "Reading",
        "Meaning",
        "Example",
        "Example_TTS",
        "Image",
      ],
    },
    { id: 200, name: "Basic", fields: ["Front", "Back", "JP_Audio"] },
  ],
  decks: [
    { id: GLOBAL_DECK_ID, name: "All Decks" },
    { id: 20, name: "JLPT N5" },
  ],
  globalDeckId: GLOBAL_DECK_ID,
  account: {
    subscription: "FREE_TRIAL_ACTIVE",
    plan: {
      planId: "free",
      planName: "Free Trial",
      notesUsed: 12,
      notesLimit: 50,
      daysLeft: 5,
      textCreditsUsed: 36,
      textCreditsCapacity: 100,
      voiceCreditsUsed: 14,
      voiceCreditsCapacity: 100,
      imageCreditsUsed: 8,
      imageCreditsCapacity: 100,
      totalCreditsUsed: 58,
      totalCreditsCapacity: 300,
    },
  },
  defaults: {
    chat: {
      provider: "auto",
      model: "auto",
      reasoningLevel: "off",
      webSearchEnabled: false,
    },
    tts: { provider: "google", model: "standard", voiceId: "en-US-Casual-K" },
    image: { provider: "openai", model: "gpt-image-1.5-low" },
  },
}

export const MOCK_CATALOG: Catalog = {
  schemaVersion: 1,
  chat: {
    providers: ["auto", "openai", "anthropic", "google"],
    models: [
      { id: "auto", provider: "auto" },
      { id: "gpt-5-mini", provider: "openai" },
      { id: "claude-sonnet-4-6", provider: "anthropic" },
      { id: "gemini-3-flash", provider: "google" },
    ],
    reasoningLevels: ["off", "low", "high"],
  },
  image: {
    providers: ["openai", "google", "replicate"],
    models: [
      { id: "gpt-image-1.5-low", provider: "openai" },
      { id: "nano-banana-2", provider: "google" },
      { id: "z-image-turbo", provider: "replicate" },
    ],
  },
}

export const setMockFixture = (fixture: string): void => {
  const state = structuredClone(BASE_STATE)

  if (fixture === "empty") state.smartFields = []
  if (fixture === "signed-out") {
    state.account = { subscription: "UNAUTHENTICATED", plan: null }
  }
  if (fixture === "paid") {
    state.account = {
      subscription: "PAID_PLAN_ACTIVE",
      plan: {
        ...state.account.plan!,
        planId: "standard",
        planName: "Standard",
        notesUsed: null,
        notesLimit: null,
        daysLeft: 18,
        totalCreditsUsed: 96,
        totalCreditsCapacity: 500,
      },
    }
  }

  useAppStore.setState({
    state,
    catalog: MOCK_CATALOG,
    connection: fixture === "reconnecting" ? "reconnecting" : "connected",
  })
}

export const handleMockCommand = (
  command: string,
  payload: Record<string, unknown>,
): void => {
  const state = useAppStore.getState().state
  if (state === null) return

  const matchesPayload = (field: SmartField) =>
    field.noteTypeId === payload.noteTypeId &&
    field.deckId === payload.deckId &&
    field.targetFieldName === payload.targetFieldName

  const smartFields =
    command === "smartFields.delete"
      ? state.smartFields.filter((field) => !matchesPayload(field))
      : state.smartFields.map((field) =>
          matchesPayload(field)
            ? { ...field, enabled: Boolean(payload.enabled) }
            : field,
        )

  useAppStore.setState({ state: { ...state, smartFields } })
}
