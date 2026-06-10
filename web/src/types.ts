// Mirrors the wire format defined in src/web/dto.py — that module is the
// source of truth for these shapes.

export interface ChatSmartFieldSettings {
  promptText: string
  provider: string
  model: string
  reasoningLevel: string
  webSearchEnabled: boolean
  usesDefaultGenerationSettings: boolean
}

export interface TTSSmartFieldSettings {
  sourceFieldName: string
  provider: string
  model: string
  voiceId: string
  usesDefaultGenerationSettings: boolean
}

export interface ImageSmartFieldSettings {
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

// Discriminated on fieldType, matching the typed settings union in
// src/models/smart_fields.py.
export type SmartField =
  | (SmartFieldBase & { fieldType: "chat"; settings: ChatSmartFieldSettings })
  | (SmartFieldBase & { fieldType: "tts"; settings: TTSSmartFieldSettings })
  | (SmartFieldBase & { fieldType: "image"; settings: ImageSmartFieldSettings })

export interface NoteType {
  id: number
  name: string
  fields: string[]
}

export interface Deck {
  id: number
  name: string
}

export interface ChatGenerationDefaults {
  provider: string
  model: string
  reasoningLevel: string
  webSearchEnabled: boolean
}

export interface TTSGenerationDefaults {
  provider: string
  model: string
  voiceId: string
}

export interface ImageGenerationDefaults {
  provider: string
  model: string
}

export interface GenerationDefaults {
  chat: ChatGenerationDefaults
  tts: TTSGenerationDefaults
  image: ImageGenerationDefaults
}

export interface AppState {
  schemaVersion: number
  smartFields: SmartField[]
  noteTypes: NoteType[]
  decks: Deck[]
  // The pseudo-deck meaning "applies to all decks".
  globalDeckId: number
  defaults: GenerationDefaults
}

export interface SelectedNote {
  id: number
  noteTypeId: number
  deckId: number | null
  fields: Record<string, string>
}

// Note contents only ship when exactly one note is selected.
export type Selection = { note: SelectedNote } | { note: null; count: number }
