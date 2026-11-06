import { bootOptions } from "@/lib/boot"
import type { CommandSender } from "@/services/commands"
import { useAppStore } from "@/store/appStore"
import type {
  AccountState,
  FreePlanReason,
  AppState,
  Catalog,
  CommandName,
  PlanInfo,
  ReviewClaimState,
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
  dailyNotesUsed: null,
  dailyNotesLimit: null,
  freePlanReason: null,
  allowedVoices: null,
  daysLeft: 5,
  totalDays: 7,
  textCreditsUsed: 36,
  textCreditsCapacity: 100,
  voiceCreditsUsed: 14,
  voiceCreditsCapacity: 100,
  imageCreditsUsed: 8,
  imageCreditsCapacity: 100,
  totalCreditsUsed: 58,
  totalCreditsCapacity: 300,
  subscriptionStatus: null,
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
      stripHtml: true,
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
      stripHtml: true,
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
      model: "gpt-image-2.5-flare-low",
      usesDefaultGenerationSettings: false,
      stripHtml: true,
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
      voiceId: "en-US-Standard-A",
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
  installId: "00000000-0000-4000-8000-000000000000",
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
  serverUnreachable: false,
  featureFlags: { reviewFreeMonth: true },
  reviewOfferUnlocked: true,
  defaults: {
    chat: {
      provider: "auto",
      model: "auto",
      reasoningLevel: "off",
      webSearchEnabled: false,
      stripHtml: true,
    },
    tts: { provider: "google", model: "standard", voiceId: "en-US-Standard-A" },
    image: {
      provider: "openai",
      model: "gpt-image-2.5-flare-low",
      stripHtml: true,
    },
  },
  settings: {
    generateAtReview: true,
    generateOnAdd: true,
    regenerateWhenBatching: false,
    debug: false,
    language: "auto",
    legacyOpenAiEnabled: false,
    legacyOpenAiKey: null,
    legacyOpenAiModel: "gpt-5-mini",
    legacyOpenAiHost: null,
    showWizardCompletion: true,
    didDismissReviewPrompt: false,
    didDismissDiscordPrompt: false,
    didSeeFreePlanWelcome: true,
    didSeeGeneratedPromptTip: false,
  },
}

const withTrialPlan = (updates: Partial<PlanInfo>): PlanInfo => ({
  ...HEALTHY_TRIAL_PLAN,
  ...updates,
})

const withFreePlan = (updates: Partial<PlanInfo>): PlanInfo =>
  withTrialPlan({
    planId: "free_mini_1",
    planType: "free",
    planName: "Free",
    notesUsed: null,
    notesLimit: null,
    dailyNotesUsed: 0,
    dailyNotesLimit: 20,
    freePlanReason: "trialExpired",
    allowedVoices: [
      { provider: "google", model: "standard", voiceIdIncludes: "-Standard-" },
    ],
    daysLeft: 21,
    totalDays: 30,
    textCreditsUsed: 300,
    textCreditsCapacity: 916,
    voiceCreditsUsed: 0,
    voiceCreditsCapacity: 916,
    imageCreditsUsed: 0,
    imageCreditsCapacity: 916,
    totalCreditsUsed: 300,
    totalCreditsCapacity: 2750,
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
  "trial-free-month": {
    status: "AUTHENTICATED",
    authToken: null,
    email: MOCK_ACCOUNT_EMAIL,
    plan: withTrialPlan({
      notesUsed: null,
      notesLimit: null,
      daysLeft: 18,
      totalDays: 30,
      textCreditsUsed: 4200,
      textCreditsCapacity: 13333,
      voiceCreditsUsed: 1100,
      voiceCreditsCapacity: 13333,
      imageCreditsUsed: 700,
      imageCreditsCapacity: 13333,
      totalCreditsUsed: 6000,
      totalCreditsCapacity: 40000,
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
  "free-daily": {
    status: "AUTHENTICATED",
    authToken: null,
    email: MOCK_ACCOUNT_EMAIL,
    plan: withFreePlan({ dailyNotesUsed: 7 }),
  },
  "free-daily-capped": {
    status: "AUTHENTICATED",
    authToken: null,
    email: MOCK_ACCOUNT_EMAIL,
    plan: withFreePlan({ dailyNotesUsed: 20 }),
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
      subscriptionStatus: "active",
    }),
  },
  "paid-canceling": {
    status: "AUTHENTICATED",
    authToken: null,
    email: MOCK_ACCOUNT_EMAIL,
    plan: withTrialPlan({
      planId: "small1",
      planType: "small",
      planName: "Lite",
      notesUsed: null,
      notesLimit: null,
      daysLeft: 30,
      textCreditsUsed: 24,
      voiceCreditsUsed: 0,
      imageCreditsUsed: 0,
      totalCreditsUsed: 24,
      totalCreditsCapacity: 300,
      subscriptionStatus: "canceling",
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
      subscriptionStatus: "expired",
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
      subscriptionStatus: "active",
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
    // Mirrors provider_model_map in src/models/providers.py.
    models: [
      { id: "auto", provider: "auto" },
      { id: "gpt-6-luna", provider: "openai" },
      { id: "gpt-6.1-terra", provider: "openai" },
      { id: "gpt-6.1-sol", provider: "openai" },
      { id: "claude-haiku-5-5", provider: "anthropic" },
      { id: "claude-sonnet-5-5", provider: "anthropic" },
      { id: "claude-opus-5-5", provider: "anthropic" },
      { id: "gemini-3.5-flash-lite", provider: "google" },
      { id: "gemini-3.8-flash", provider: "google" },
      { id: "gemini-4-argon", provider: "google" },
    ],
    reasoningLevels: ["off", "low", "high", "max"],
  },
  image: {
    providers: ["openai", "google", "replicate"],
    models: [
      { id: "gpt-image-2.5-flare-low", provider: "openai" },
      { id: "gpt-image-2.5-flare-medium", provider: "openai" },
      { id: "gpt-image-2.5-sunburst-low", provider: "openai" },
      { id: "gpt-image-2.5-sunburst-medium", provider: "openai" },
      { id: "nano-banana-2-lite", provider: "google" },
      { id: "nano-banana-2.1", provider: "google" },
      { id: "z-image-turbo", provider: "replicate" },
    ],
  },
}

export const MOCK_VOICE_CATALOG: VoiceCatalog = {
  voices: [
    {
      provider: "google",
      voiceId: "en-US-Standard-C",
      model: "standard",
      name: "English (United States) - Female (Standard)",
      gender: "Female",
      language: "English (United States)",
      priceTier: "low",
    },
    {
      provider: "google",
      voiceId: "en-US-Standard-A",
      model: "standard",
      name: "English (United States) - Male (Standard)",
      gender: "Male",
      language: "English (United States)",
      priceTier: "low",
    },
    {
      provider: "google",
      voiceId: "ja-JP-Chirp3-HD-Achernar",
      model: "chirp",
      name: "Japanese - Female Achernar (Chirp 3 HD)",
      gender: "Female",
      language: "Japanese",
      priceTier: "standard",
    },
    {
      provider: "google",
      voiceId: "ja-JP-Standard-A",
      model: "standard",
      name: "Japanese - Female (Standard)",
      gender: "Female",
      language: "Japanese",
      priceTier: "low",
    },
    {
      provider: "google",
      voiceId: "ja-JP-Standard-C",
      model: "standard",
      name: "Japanese - Male (Standard)",
      gender: "Male",
      language: "Japanese",
      priceTier: "low",
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

// The plugin reads a following field's settings from the defaults, so saving the
// defaults changes every field that follows them.
const followDefaults = (
  fields: SmartField[],
  fieldType: SmartField["fieldType"],
  defaults: unknown,
): SmartField[] =>
  fields.map((field) =>
    field.fieldType === fieldType &&
    field.settings.usesDefaultGenerationSettings
      ? ({
          ...field,
          settings: { ...field.settings, ...(defaults as object) },
        } as SmartField)
      : field,
  )

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

const FREE_STARTED_FIXTURES: Record<string, FreePlanReason> = {
  "free-started": "trialExpired",
  "free-started-notes": "trialNotes",
  "free-started-credits": "trialCredits",
  "free-started-access": "accessEnded",
}

export const setMockFixture = (fixture: string): void => {
  const state = structuredClone(BASE_STATE)

  if (fixture === "empty" || fixture === "signed-out-empty") {
    state.smartFields = []
  }
  if (fixture in MOCK_ACCOUNT_FIXTURES) {
    state.account = structuredClone(MOCK_ACCOUNT_FIXTURES[fixture])
  }
  // The first open after a user drops to the free plan, for each reason.
  const freeStartedReason = FREE_STARTED_FIXTURES[fixture]
  if (freeStartedReason !== undefined) {
    state.account = {
      ...structuredClone(MOCK_ACCOUNT_FIXTURES["free-daily"]),
      plan: withFreePlan({ freePlanReason: freeStartedReason }),
    } as AccountState
    state.settings.didSeeFreePlanWelcome = false
  }
  if (
    state.account.status === "AUTHENTICATED" &&
    state.account.plan.planType === "free"
  ) {
    // One text field pinned to settings the free plan doesn't include, and a
    // voice field on a voice it doesn't include but can stand in for.
    state.smartFields = state.smartFields.map((field) => {
      if (field.id === "meaning" && field.fieldType === "chat") {
        return {
          ...field,
          settings: {
            ...field.settings,
            reasoningLevel: "high",
            webSearchEnabled: true,
            usesDefaultGenerationSettings: false,
          },
        }
      }
      if (field.id === "audio-off" && field.fieldType === "tts") {
        return {
          ...field,
          enabled: true,
          settings: {
            ...field.settings,
            model: "chirp",
            voiceId: "ja-JP-Chirp3-HD-Achernar",
            usesDefaultGenerationSettings: false,
          },
        }
      }
      return field
    })
  }
  // A failed startup refresh leaves the account loading.
  if (fixture === "server-unreachable") {
    state.account = structuredClone(MOCK_ACCOUNT_FIXTURES.loading)
    state.serverUnreachable = true
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

let mockReviewClaimState: ReviewClaimState = "available"

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

  if (command === "notes.randomTestCard") {
    return (Object.values(MOCK_SELECTIONS).find(
      (selection) => selection.note?.noteTypeId === commandPayload.noteTypeId,
    ) ?? MOCK_SELECTIONS.none) as Result
  }

  if (command === "prompts.suggest") {
    await new Promise((resolve) => setTimeout(resolve, 600))
    return {
      suggestion:
        commandPayload.fieldType === "image"
          ? "Draw a simple scene that shows Expression"
          : "Translate Expression into natural English",
    } as Result
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

  if (command === "reviewClaim.get") {
    // Like the server, paid users can't get the free month.
    const planType =
      state.account.status === "AUTHENTICATED"
        ? state.account.plan.planType
        : null
    const paid =
      planType === "small" || planType === "medium" || planType === "large"
    return {
      state: paid ? "unavailable" : mockReviewClaimState,
    } as Result
  }

  if (command === "reviewClaim.send") {
    await new Promise((resolve) => setTimeout(resolve, 500))
    if (commandPayload.step === "claim") mockReviewClaimState = "claimed"
    return { state: mockReviewClaimState } as Result
  }

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
        smartFields: followDefaults(state.smartFields, "chat", commandPayload),
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
        smartFields: followDefaults(state.smartFields, "image", commandPayload),
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
        smartFields: followDefaults(state.smartFields, "tts", commandPayload),
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
