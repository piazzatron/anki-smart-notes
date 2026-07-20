import { modelLabel, providerLabel } from "@/lib/catalog"

import type { SmartField } from "./types"

export const smartFieldDescription = (field: SmartField): string => {
  if (field.fieldType === "tts") {
    return `Reads {{${field.settings.sourceFieldName}}} aloud`
  }

  return field.settings.promptText
}

export const smartFieldModelLabel = (field: SmartField): string => {
  const isDefault = field.settings.usesDefaultGenerationSettings

  if (field.fieldType === "tts") {
    const voice = field.settings.voiceId
    const label = `${providerLabel(field.settings.provider)} · ${voice}`
    return isDefault ? `Default · ${label}` : label
  }

  const label = modelLabel(field.settings.model)
  if (isDefault && field.settings.model === "auto") return "✦ Auto"
  return isDefault ? `Default · ${label}` : label
}
