import { useEffect, useState } from "react"

import { errorMessage } from "@/lib/errors"
import { getVoiceCatalog } from "@/services/voiceCatalog"
import type { VoiceCatalog } from "@/types/api"

export const useVoiceCatalog = () => {
  const [catalog, setCatalog] = useState<VoiceCatalog | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let active = true
    void getVoiceCatalog()
      .then((result) => {
        if (active) setCatalog(result)
      })
      .catch((reason: unknown) => {
        if (active) {
          setError(errorMessage(reason, "Could not load voices"))
        }
      })
    return () => {
      active = false
    }
  }, [])

  return { catalog, error }
}
