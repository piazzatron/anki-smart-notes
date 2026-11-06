import { create } from "zustand"

import type { AppState, Catalog, Selection } from "@/types/api"

export type Connection = "connecting" | "connected" | "reconnecting"

interface AppStore {
  connection: Connection
  state: AppState | null
  catalog: Catalog | null
  selection: Selection | null
  // The guide to generating a Smart Field, shown for the rest of the window session
  // in which the user saved one when they had none: "new" until it has celebrated
  // once, then "seen".
  firstFieldGuide: "new" | "seen" | null
}

export const useAppStore = create<AppStore>(() => ({
  connection: "connecting",
  state: null,
  catalog: null,
  selection: null,
  firstFieldGuide: null,
}))
