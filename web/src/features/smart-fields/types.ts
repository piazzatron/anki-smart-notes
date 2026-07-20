interface ChatSmartFieldSettings {
  promptText: string
  provider: string
  model: string
  reasoningLevel: string
  webSearchEnabled: boolean
  usesDefaultGenerationSettings: boolean
}

interface TTSSmartFieldSettings {
  sourceFieldName: string
  provider: string
  model: string
  voiceId: string
  usesDefaultGenerationSettings: boolean
}

interface ImageSmartFieldSettings {
  promptText: string
  provider: string
  model: string
  usesDefaultGenerationSettings: boolean
}

interface SmartFieldBase {
  id: string
  noteTypeId: number
  deckId: number
  targetFieldName: string
  enabled: boolean
}

export type SmartField =
  | (SmartFieldBase & { fieldType: "chat"; settings: ChatSmartFieldSettings })
  | (SmartFieldBase & { fieldType: "tts"; settings: TTSSmartFieldSettings })
  | (SmartFieldBase & {
      fieldType: "image"
      settings: ImageSmartFieldSettings
    })
