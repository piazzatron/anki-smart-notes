import { bootOptions } from "@/lib/boot"
import type { VoiceCatalog } from "@/types/api"

// One request for every caller, including ones that ask before it resolves.
let cachedCatalog: Promise<VoiceCatalog> | null = null

export const getVoiceCatalog = (): Promise<VoiceCatalog> => {
  cachedCatalog ??= loadVoiceCatalog().catch((error: unknown) => {
    cachedCatalog = null
    throw error
  })
  return cachedCatalog
}

const loadVoiceCatalog = async (): Promise<VoiceCatalog> => {
  if (bootOptions.mock) {
    const { MOCK_VOICE_CATALOG } = await import("@/dev/mockData")
    return MOCK_VOICE_CATALOG
  }

  const response = await fetch("/app/voice-catalog.json")
  if (!response.ok) {
    throw new Error(`Could not load voices (${response.status})`)
  }
  return (await response.json()) as VoiceCatalog
}
