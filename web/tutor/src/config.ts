export type TutorConfig = {
  serverUrl: string
  jwt: string
}

declare global {
  interface Window {
    __TUTOR_CONFIG__?: TutorConfig
  }
}

// In dev (vite dev server), point at the local backend with no auth so the
// UI can be iterated on in a browser. The Python dialog overrides this by
// injecting __TUTOR_CONFIG__ into the page before the bundle runs.
const DEV_FALLBACK: TutorConfig = {
  serverUrl: "http://localhost:3000",
  jwt: "",
}

export const config: TutorConfig = window.__TUTOR_CONFIG__ ?? DEV_FALLBACK
