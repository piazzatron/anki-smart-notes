import { create } from "zustand"

import type { AccountState } from "@/components/shared/planPresentation"
import type { SmartField } from "@/features/smart-fields/types"

export type Connection = "connecting" | "connected" | "reconnecting"

export interface AppState {
  schemaVersion: number
  smartFields: SmartField[]
  noteTypes: Array<{ id: number; name: string; fields: string[] }>
  decks: Array<{ id: number; name: string }>
  globalDeckId: number
  account: AccountState
  defaults: {
    chat: {
      provider: string
      model: string
      reasoningLevel: string
      webSearchEnabled: boolean
    }
    tts: { provider: string; model: string; voiceId: string }
    image: { provider: string; model: string }
  }
}

export interface Catalog {
  schemaVersion: number
  chat: {
    providers: string[]
    models: Array<{ id: string; provider: string }>
    reasoningLevels: string[]
  }
  image: {
    providers: string[]
    models: Array<{ id: string; provider: string }>
  }
}

interface SelectedNote {
  id: number
  noteTypeId: number
  deckId: number | null
  fields: Record<string, string>
}

export type Selection = { note: SelectedNote } | { note: null; count: number }

interface AppStore {
  connection: Connection
  state: AppState | null
  catalog: Catalog | null
  selection: Selection | null
}

export const useAppStore = create<AppStore>(() => ({
  connection: "connecting",
  state: null,
  catalog: null,
  selection: null,
}))
