import { useEffect, useState } from "react"
import { useTranslation } from "react-i18next"

import { errorMessage } from "@/lib/errors"
import { getVoiceCatalog } from "@/services/voiceCatalog"
import type { VoiceCatalog } from "@/types/api"

export const useVoiceCatalog = () => {
  const { t } = useTranslation()
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
          setError(errorMessage(reason, t("defaults.voice.cannotLoad")))
        }
      })
    return () => {
      active = false
    }
  }, [t])

  return { catalog, error }
}
