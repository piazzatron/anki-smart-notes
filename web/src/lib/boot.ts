export type ScreenId =
  | "fields"
  | "defaults-text"
  | "defaults-images"
  | "defaults-voice"
  | "generation"
  | "advanced"
  | "subscription"
  | "support"

const SCREEN_IDS = new Set<ScreenId>([
  "fields",
  "defaults-text",
  "defaults-images",
  "defaults-voice",
  "generation",
  "advanced",
  "subscription",
  "support",
])

interface BootOptions {
  screen: ScreenId
  mock: boolean
  fixture: string
}

export const readBootOptions = (): BootOptions => {
  const params = new URLSearchParams(window.location.search)
  const requestedScreen = params.get("screen")

  return {
    screen:
      requestedScreen !== null && SCREEN_IDS.has(requestedScreen as ScreenId)
        ? (requestedScreen as ScreenId)
        : "fields",
    mock: import.meta.env.DEV && params.get("mock") === "1",
    fixture: params.get("fixture") ?? "populated",
  }
}
