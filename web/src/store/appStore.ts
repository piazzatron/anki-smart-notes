import { create } from "zustand"

import type { AppState, Catalog, ReviewerCard, Selection } from "@/types/api"

export type Connection = "connecting" | "connected" | "reconnecting"

interface AppStore {
  connection: Connection
  state: AppState | null
  catalog: Catalog | null
  selection: Selection | null
  reviewerCard: ReviewerCard | null
}

export const useAppStore = create<AppStore>(() => ({
  connection: "connecting",
  state: null,
  catalog: null,
  selection: null,
  reviewerCard: null,
}))
