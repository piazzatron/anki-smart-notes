import { create } from "zustand"

import type { AppState, Selection } from "./types"

export type Connection = "connecting" | "connected" | "reconnecting"

interface AppStore {
  connection: Connection
  // The last `state` event, replaced wholesale. The SSE client is the only
  // writer of domain state — components never write to this store.
  state: AppState | null
  selection: Selection | null
}

export const useStore = create<AppStore>(() => ({
  connection: "connecting",
  state: null,
  selection: null,
}))
