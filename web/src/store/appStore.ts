import { create } from "zustand"

import type { AppState, Catalog, Selection } from "@/types/api"

export type Connection = "connecting" | "connected" | "reconnecting"

interface AppStore {
  connection: Connection
  state: AppState | null
  catalog: Catalog | null
  selection: Selection | null
  // Whether the guide to generating a Smart Field is open: it pops up when the user
  // saves one while they had none.
  firstFieldGuide: boolean
}

export const useAppStore = create<AppStore>(() => ({
  connection: "connecting",
  state: null,
  catalog: null,
  selection: null,
  firstFieldGuide: false,
}))
