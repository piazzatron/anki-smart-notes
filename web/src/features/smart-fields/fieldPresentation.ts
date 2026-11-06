import {
  chatModelLabel,
  freePlanChatSettings,
  isPaidOnlyChatSettings,
} from "@/features/text-generation/intelligence"
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

/** The model or voice a field runs with. On the free plan, paid-only text settings
 *  run as Auto Standard. A field that follows the defaults carries them as its own
 *  settings, so this names the default too. */
export const smartFieldModelLabel = (
  field: SmartField,
  isFree: boolean,
): string => {
  if (field.fieldType === "tts") {
    return `${providerLabel(field.settings.provider)} · ${field.settings.voiceId}`
  }
  if (field.fieldType === "image") return modelLabel(field.settings.model)

  return chatModelLabel(
    isFree && isPaidOnlyChatSettings(field.settings)
      ? freePlanChatSettings(field.settings)
      : field.settings,
  )
}
