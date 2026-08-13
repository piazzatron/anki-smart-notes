import { modelLabel, providerLabel } from "@/lib/catalog"
import type { SmartField } from "@/types/api"

export const smartFieldDescription = (field: SmartField): string => {
  if (field.fieldType === "tts") {
    return `Reads {{${field.settings.sourceFieldName}}} aloud`
  }

  return field.settings.promptText
}

export const smartFieldModelLabel = (field: SmartField): string => {
  if (field.settings.usesDefaultGenerationSettings) {
    return "Default"
  }

  if (field.fieldType === "tts") {
    const voice = field.settings.voiceId
    return `${providerLabel(field.settings.provider)} · ${voice}`
  }

  return modelLabel(field.settings.model)
}
