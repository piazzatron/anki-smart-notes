export type ScreenId =
  | "fields"
  | "defaults-text"
  | "defaults-images"
  | "defaults-voice"
  | "settings"
  | "subscription"
  | "support"

const SCREEN_IDS = new Set<ScreenId>([
  "fields",
  "defaults-text",
  "defaults-images",
  "defaults-voice",
  "settings",
  "subscription",
  "support",
])

interface BootOptions {
  screen: ScreenId
  mock: boolean
  fixture: string
  selection: string
  tryState: "empty" | "picked" | "result" | null
  token: string
}

const readBootOptions = (): BootOptions => {
  const params = new URLSearchParams(window.location.search)
  const requestedScreen = params.get("screen")
  const requestedTryState = params.get("try")

  return {
    screen:
      requestedScreen !== null && SCREEN_IDS.has(requestedScreen as ScreenId)
        ? (requestedScreen as ScreenId)
        : "fields",
    mock: import.meta.env.DEV && params.get("mock") === "1",
    fixture: params.get("fixture") ?? "populated",
    selection: params.get("selection") ?? "selected",
    tryState:
      requestedTryState === "empty" ||
      requestedTryState === "picked" ||
      requestedTryState === "result"
        ? requestedTryState
        : null,
    token: params.get("token") ?? "",
  }
}

export const bootOptions = Object.freeze(readBootOptions())
