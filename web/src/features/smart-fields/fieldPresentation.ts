import { modelLabel, providerLabel } from "@/lib/catalog"
import i18next from "i18next"
import type { SmartField } from "@/types/api"

export const smartFieldDescription = (field: SmartField): string => {
  if (field.fieldType === "tts") {
    return i18next.t("smartFields.readsAloud", {
      field: `{{${field.settings.sourceFieldName}}}`,
    })
  }

  return field.settings.promptText
}

export const smartFieldModelLabel = (field: SmartField): string => {
  if (field.settings.usesDefaultGenerationSettings) {
    return i18next.t("common.default")
  }

  if (field.fieldType === "tts") {
    const voice = field.settings.voiceId
    return `${providerLabel(field.settings.provider)} · ${voice}`
  }

  return modelLabel(field.settings.model)
}
