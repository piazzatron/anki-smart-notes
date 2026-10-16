import { create } from "zustand"

import type { ScreenId } from "@/lib/boot"

import type {
  AppState,
  AssistantActiveTarget,
  Catalog,
  Selection,
} from "@/types/api"

export type Connection = "connecting" | "connected" | "reconnecting"

interface AppStore {
  connection: Connection
  state: AppState | null
  catalog: Catalog | null
  selection: Selection | null
  activeTarget: AssistantActiveTarget | null
  /** A screen the plugin asked for, cleared once the shell has navigated. */
  requestedScreen: ScreenId | null
}

export const useAppStore = create<AppStore>(() => ({
  connection: "connecting",
  state: null,
  catalog: null,
  selection: null,
  activeTarget: null,
  requestedScreen: null,
}))
