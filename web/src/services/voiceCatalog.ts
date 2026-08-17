import { bootOptions } from "@/lib/boot"
import type { VoiceCatalog } from "@/types/api"

let cachedCatalog: VoiceCatalog | null = null

export const getVoiceCatalog = async (): Promise<VoiceCatalog> => {
  if (cachedCatalog !== null) return cachedCatalog

  if (bootOptions.mock) {
    const { MOCK_VOICE_CATALOG } = await import("@/dev/mockData")
    cachedCatalog = MOCK_VOICE_CATALOG
    return cachedCatalog
  }

  const response = await fetch("/app/voice-catalog.json")
  if (!response.ok) {
    throw new Error(`Could not load voices (${response.status})`)
  }
  cachedCatalog = (await response.json()) as VoiceCatalog
  return cachedCatalog
}
