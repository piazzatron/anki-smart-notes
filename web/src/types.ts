// Mirrors the wire format defined in src/web/dto.py — that module is the
// source of truth for these shapes.

export interface SmartField {
  id: string
  noteTypeId: number
  deckId: number
  targetFieldName: string
  fieldType: "chat" | "tts" | "image"
  enabled: boolean
  settings: Record<string, unknown>
}

export interface NoteType {
  id: number
  name: string
  fields: string[]
}

export interface Deck {
  id: number
  name: string
}

export interface AppState {
  schemaVersion: number
  smartFields: SmartField[]
  noteTypes: NoteType[]
  decks: Deck[]
  // The pseudo-deck meaning "applies to all decks".
  globalDeckId: number
  defaults: Record<string, Record<string, unknown>>
}

export interface SelectedNote {
  id: number
  noteTypeId: number
  deckId: number | null
  fields: Record<string, string>
}

// Note contents only ship when exactly one note is selected.
export type Selection = { note: SelectedNote } | { note: null; count: number }
