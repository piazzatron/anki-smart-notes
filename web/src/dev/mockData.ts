import { bootOptions } from "@/lib/boot"
import type { CommandSender } from "@/services/commands"
import { useAppStore } from "@/store/appStore"
import type {
  AppState,
  Catalog,
  CommandName,
  Selection,
  SmartField,
  VoiceCatalog,
} from "@/types/api"

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
      { id: "gpt-image-2-low", provider: "openai" },
      { id: "gpt-image-1.5-medium", provider: "openai" },
      { id: "gpt-image-2-medium", provider: "openai" },
      { id: "nano-banana-2", provider: "google" },
      { id: "z-image-turbo", provider: "replicate" },
      { id: "flux-dev", provider: "replicate" },
    ],
  },
}

export const MOCK_VOICE_CATALOG: VoiceCatalog = {
  schemaVersion: 1,
  voices: [
    {
      provider: "google",
      voiceId: "en-US-Casual-K",
      model: "standard",
      name: "English (United States) - Male (Standard)",
      gender: "Male",
      language: "English (United States)",
      priceTier: "low",
    },
    {
      provider: "google",
      voiceId: "ja-JP-Neural2-B",
      model: "neural",
      name: "Japanese - Female (Neural)",
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
      provider: "elevenLabs",
      voiceId: "EXAVITQu4vr4xnSDxMaL",
      model: "eleven_multilingual_v2",
      name: "Sarah (Multilingual V2)",
      gender: "Female",
      language: "English (United States)",
      priceTier: "ultra-high",
    },
    {
      provider: "azure",
      voiceId: "en-US-JennyNeural",
      model: "neural",
      name: "Jenny (Neural)",
      gender: "Female",
      language: "English",
      priceTier: "standard",
    },
    {
      provider: "voicevox",
      voiceId: "2",
      model: "voicevox",
      name: "Shikoku Metan (Normal)",
      gender: "Female",
      language: "Japanese",
      priceTier: "free",
    },
  ],
}

const MOCK_IMAGE_DATA_URL =
  "data:image/svg+xml;charset=utf-8,%3Csvg xmlns='http://www.w3.org/2000/svg' width='960' height='640' viewBox='0 0 960 640'%3E%3Cdefs%3E%3ClinearGradient id='g' x1='0' y1='0' x2='1' y2='1'%3E%3Cstop stop-color='%232b3149'/%3E%3Cstop offset='1' stop-color='%23121825'/%3E%3C/linearGradient%3E%3C/defs%3E%3Crect width='960' height='640' fill='url(%23g)'/%3E%3Ccircle cx='720' cy='190' r='100' fill='%238bd3a8' opacity='.78'/%3E%3Cpath d='M120 500 Q330 220 500 500 T900 500' fill='none' stroke='%239ba8ff' stroke-width='28' stroke-linecap='round'/%3E%3Ctext x='70' y='105' fill='%23f4f4f5' font-family='sans-serif' font-size='42' font-weight='700'%3EA memorable scene for 食べる%3C/text%3E%3C/svg%3E"

const MOCK_AUDIO_DATA_URL =
  "data:audio/wav;base64,UklGRiQAAABXQVZFZm10IBAAAAABAAEAQB8AAEAfAAABAAgAZGF0YQAAAAA="

const MOCK_SELECTIONS: Record<string, Selection> = {
  selected: {
    note: {
      cardId: 9001,
      id: 501,
      noteTypeId: 100,
      deckId: 20,
      fields: {
        Expression: "食べる",
        Reading: "たべる",
        Meaning: "to eat",
        Example: "りんごを食べる。",
        Example_TTS: "",
        Image: "",
      },
    },
  },
  none: { note: null, count: 0 },
  multiple: { note: null, count: 3 },
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
    selection:
      bootOptions.tryState === "empty"
        ? MOCK_SELECTIONS.none
        : bootOptions.tryState === "picked" || bootOptions.tryState === "result"
          ? MOCK_SELECTIONS.selected
          : (MOCK_SELECTIONS[bootOptions.selection] ??
            MOCK_SELECTIONS.selected),
    connection: fixture === "reconnecting" ? "reconnecting" : "connected",
  })
}

export const setMockSelection = (selection: string): void => {
  useAppStore.setState({
    selection: MOCK_SELECTIONS[selection] ?? MOCK_SELECTIONS.selected,
  })
}

export const sendMockCommand: CommandSender = async <Result = void>(
  command: CommandName,
  payload: object,
): Promise<Result> => {
  if (command === "ui.openBrowser") return undefined as Result

  const state = useAppStore.getState().state
  if (state === null) return undefined as Result
  const commandPayload = payload as Record<string, unknown>

  if (command === "prompts.test") {
    return {
      text: "To eat — the act of consuming food, as in りんごを食べる (to eat an apple).",
    } as Result
  }

  if (command === "images.test") {
    return { dataUrl: MOCK_IMAGE_DATA_URL } as Result
  }

  if (command === "tts.test" || command === "tts.preview") {
    return { dataUrl: MOCK_AUDIO_DATA_URL } as Result
  }

  if (command === "defaults.chat.save") {
    useAppStore.setState({
      state: {
        ...state,
        defaults: {
          ...state.defaults,
          chat: commandPayload as unknown as AppState["defaults"]["chat"],
        },
      },
    })
    return undefined as Result
  }

  if (command === "defaults.image.save") {
    useAppStore.setState({
      state: {
        ...state,
        defaults: {
          ...state.defaults,
          image: commandPayload as unknown as AppState["defaults"]["image"],
        },
      },
    })
    return undefined as Result
  }

  if (command === "defaults.tts.save") {
    useAppStore.setState({
      state: {
        ...state,
        defaults: {
          ...state.defaults,
          tts: commandPayload as unknown as AppState["defaults"]["tts"],
        },
      },
    })
    return undefined as Result
  }

  const matchesPayload = (field: SmartField) =>
    field.noteTypeId === commandPayload.noteTypeId &&
    field.deckId === commandPayload.deckId &&
    field.targetFieldName === commandPayload.targetFieldName

  const smartFields =
    command === "smartFields.delete"
      ? state.smartFields.filter((field) => !matchesPayload(field))
      : state.smartFields.map((field) =>
          matchesPayload(field)
            ? { ...field, enabled: Boolean(commandPayload.enabled) }
            : field,
        )

  useAppStore.setState({ state: { ...state, smartFields } })
  return undefined as Result
}
