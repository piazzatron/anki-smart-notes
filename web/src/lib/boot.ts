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
  editor: "create" | "edit" | "duplicate" | null
  editorStep: 1 | 2 | 3 | null
  token: string
  locale: string
  ankiLocale: string
}

const readBootOptions = (): BootOptions => {
  const params = new URLSearchParams(
    typeof window === "undefined" ? "" : window.location.search,
  )
  const browserLocale =
    typeof navigator === "undefined" ? "en" : navigator.language
  const requestedScreen = params.get("screen")
  const requestedTryState = params.get("try")
  const requestedEditor = params.get("editor")
  const requestedEditorStep = Number(params.get("step"))

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
    editor:
      requestedEditor === "create" ||
      requestedEditor === "edit" ||
      requestedEditor === "duplicate"
        ? requestedEditor
        : null,
    editorStep:
      requestedEditorStep === 1 ||
      requestedEditorStep === 2 ||
      requestedEditorStep === 3
        ? requestedEditorStep
        : null,
    token: params.get("token") ?? "",
    locale:
      params.get("locale") ?? (import.meta.env.DEV ? browserLocale : "en"),
    ankiLocale:
      params.get("ankiLocale") ??
      params.get("locale") ??
      (import.meta.env.DEV ? browserLocale : "en"),
  }
}

export const bootOptions = Object.freeze(readBootOptions())
