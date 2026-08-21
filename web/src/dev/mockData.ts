import { bootOptions } from "@/lib/boot"
import type { CommandSender } from "@/services/commands"
import { useAppStore } from "@/store/appStore"
import type {
  AccountState,
  AppState,
  Catalog,
  CommandName,
  PlanInfo,
  Selection,
  SmartField,
  SmartFieldCreatePayload,
  SmartFieldUpdatePayload,
  VoiceCatalog,
} from "@/types/api"

const GLOBAL_DECK_ID = 1
const MOCK_ACCOUNT_EMAIL = "geniie.dev@gmail.com"

const HEALTHY_TRIAL_PLAN: PlanInfo = {
  planId: "free",
  planType: "trial",
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
}

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
  appVersion: "1.5.0-dev",
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
    status: "AUTHENTICATED",
    plan: HEALTHY_TRIAL_PLAN,
    email: MOCK_ACCOUNT_EMAIL,
    authToken: null,
  },
  featureFlags: { reviewFreeMonth: true },
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
  settings: {
    generateAtReview: true,
    regenerateWhenBatching: false,
    debug: false,
    legacyOpenAiEnabled: false,
    legacyOpenAiKey: null,
    legacyOpenAiModel: "gpt-5-mini",
    legacyOpenAiHost: null,
    showWizardCompletion: true,
    didDismissReviewPrompt: false,
    didDismissDiscordPrompt: false,
  },
}

const withTrialPlan = (updates: Partial<PlanInfo>): PlanInfo => ({
  ...HEALTHY_TRIAL_PLAN,
  ...updates,
})

export const MOCK_ACCOUNT_FIXTURES: Record<string, AccountState> = {
  "signed-out-empty": {
    status: "UNAUTHENTICATED",
    plan: null,
    email: null,
    authToken: null,
  },
  "trial-healthy": {
    status: "AUTHENTICATED",
    plan: HEALTHY_TRIAL_PLAN,
    email: MOCK_ACCOUNT_EMAIL,
    authToken: null,
  },
  "trial-ending": {
    status: "AUTHENTICATED",
    authToken: null,
    email: MOCK_ACCOUNT_EMAIL,
    plan: withTrialPlan({
      daysLeft: 2,
      notesUsed: 42,
      textCreditsUsed: 85,
      voiceCreditsUsed: 75,
      imageCreditsUsed: 86,
      totalCreditsUsed: 246,
    }),
  },
  "trial-expired": {
    status: "AUTHENTICATED",
    plan: withTrialPlan({ daysLeft: 0, notesUsed: 50 }),
    email: MOCK_ACCOUNT_EMAIL,
    authToken: null,
  },
  "trial-capacity": {
    status: "AUTHENTICATED",
    authToken: null,
    email: MOCK_ACCOUNT_EMAIL,
    plan: withTrialPlan({
      notesUsed: 50,
      textCreditsUsed: 100,
      voiceCreditsUsed: 100,
      imageCreditsUsed: 100,
      totalCreditsUsed: 300,
    }),
  },
  free: {
    status: "AUTHENTICATED",
    authToken: null,
    email: MOCK_ACCOUNT_EMAIL,
    plan: withTrialPlan({
      planId: "free_mini_1",
      planType: "freemium",
      planName: "Free",
      notesUsed: null,
      notesLimit: null,
      daysLeft: 8,
      textCreditsUsed: 40,
      textCreditsCapacity: 70,
      voiceCreditsUsed: 12,
      voiceCreditsCapacity: 20,
      imageCreditsUsed: 10,
      imageCreditsCapacity: 10,
      totalCreditsUsed: 62,
      totalCreditsCapacity: 100,
    }),
  },
  paid: {
    status: "AUTHENTICATED",
    authToken: null,
    email: MOCK_ACCOUNT_EMAIL,
    plan: withTrialPlan({
      planId: "medium1",
      planType: "medium",
      planName: "Standard",
      notesUsed: null,
      notesLimit: null,
      daysLeft: 18,
      textCreditsUsed: 70,
      textCreditsCapacity: 250,
      voiceCreditsUsed: 3,
      voiceCreditsCapacity: 100,
      imageCreditsUsed: 97,
      imageCreditsCapacity: 150,
      totalCreditsUsed: 170,
      totalCreditsCapacity: 500,
    }),
  },
  "paid-expired": {
    status: "AUTHENTICATED",
    authToken: null,
    email: MOCK_ACCOUNT_EMAIL,
    plan: withTrialPlan({
      planId: "medium1",
      planType: "medium",
      planName: "Standard",
      notesUsed: null,
      notesLimit: null,
      daysLeft: 0,
    }),
  },
  "paid-capacity": {
    status: "AUTHENTICATED",
    authToken: null,
    email: MOCK_ACCOUNT_EMAIL,
    plan: withTrialPlan({
      planId: "large1",
      planType: "large",
      planName: "Pro",
      notesUsed: null,
      notesLimit: null,
      textCreditsUsed: 250,
      textCreditsCapacity: 250,
      voiceCreditsUsed: 100,
      voiceCreditsCapacity: 100,
      imageCreditsUsed: 150,
      imageCreditsCapacity: 150,
      totalCreditsUsed: 500,
      totalCreditsCapacity: 500,
    }),
  },
  "signed-out": {
    status: "UNAUTHENTICATED",
    plan: null,
    email: null,
    authToken: null,
  },
  loading: { status: "LOADING", plan: null, email: null, authToken: null },
}

export const MOCK_CATALOG: Catalog = {
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
  // A Basic note — the wrong note type for the Japanese smart fields, so the tester
  // shows its wrong-note-type state.
  mismatch: {
    note: {
      cardId: 9002,
      id: 502,
      noteTypeId: 200,
      deckId: 20,
      fields: { Front: "eat", Back: "食べる", JP_Audio: "" },
    },
  },
  none: { note: null, count: 0 },
  multiple: { note: null, count: 3 },
}

export const setMockFixture = (fixture: string): void => {
  const state = structuredClone(BASE_STATE)

  if (fixture === "empty" || fixture === "signed-out-empty") {
    state.smartFields = []
  }
  if (fixture in MOCK_ACCOUNT_FIXTURES) {
    state.account = structuredClone(MOCK_ACCOUNT_FIXTURES[fixture])
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

  if (command === "auth.exchangeCode") {
    await new Promise((resolve) => setTimeout(resolve, 500))
    useAppStore.setState({
      state: {
        ...state,
        account: structuredClone(MOCK_ACCOUNT_FIXTURES["trial-healthy"]),
      },
    })
    return undefined as Result
  }

  if (command === "prompts.test") {
    return {
      text: "To eat — the act of consuming food, as in りんごを食べる (to eat an apple).",
      resultToken: `mock-token-${Date.now()}`,
    } as Result
  }

  if (command === "images.test") {
    return {
      dataUrl: MOCK_IMAGE_DATA_URL,
      resultToken: `mock-token-${Date.now()}`,
    } as Result
  }

  if (command === "tts.test") {
    return {
      dataUrl: MOCK_AUDIO_DATA_URL,
      ...(commandPayload.cardId === undefined
        ? {}
        : { resultToken: `mock-token-${Date.now()}` }),
    } as Result
  }

  if (command === "notes.saveTestResult") {
    await new Promise((resolve) => setTimeout(resolve, 400))
    return undefined as Result
  }

  if (command === "prompts.generate") {
    await new Promise((resolve) => setTimeout(resolve, 600))
    return {
      prompt:
        commandPayload.fieldType === "image"
          ? "A vivid, memorable scene illustrating {{Expression}}. No text or labels."
          : "Translate {{Expression}} into natural English. Return only the translation.",
    } as Result
  }

  if (command === "settings.save") {
    useAppStore.setState({
      state: {
        ...state,
        settings: commandPayload as unknown as AppState["settings"],
      },
    })
    return undefined as Result
  }

  if (command === "support.sendFeedback") return undefined as Result

  if (command === "account.refresh") return undefined as Result

  if (command === "auth.logout") {
    useAppStore.setState({
      state: {
        ...state,
        account: {
          status: "UNAUTHENTICATED",
          plan: null,
          email: null,
          authToken: null,
        },
      },
    })
    return undefined as Result
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

  if (command === "smartFields.create") {
    const createdField = payload as SmartFieldCreatePayload
    const fieldWithId: SmartField = {
      ...createdField,
      id: `mock-${createdField.noteTypeId}-${createdField.deckId}-${createdField.targetFieldName}`,
    }

    useAppStore.setState({
      state: {
        ...state,
        smartFields: [...state.smartFields, fieldWithId],
      },
    })
    return undefined as Result
  }

  if (command === "smartFields.update") {
    const updatedField = payload as SmartFieldUpdatePayload
    useAppStore.setState({
      state: {
        ...state,
        smartFields: state.smartFields.map((field) =>
          field.id === updatedField.id ? updatedField : field,
        ),
      },
    })
    return undefined as Result
  }

  const smartFields =
    command === "smartFields.delete"
      ? state.smartFields.filter((field) => field.id !== commandPayload.id)
      : state.smartFields.map((field) =>
          field.id === commandPayload.id
            ? { ...field, enabled: Boolean(commandPayload.enabled) }
            : field,
        )

  useAppStore.setState({ state: { ...state, smartFields } })
  return undefined as Result
}
