import {
  chatModelLabel,
  freePlanChatSettings,
  isPaidOnlyChatSettings,
} from "@/features/text-generation/intelligence"
import { voiceMatchesSettings } from "@/features/defaults/voiceDefaults"
import { modelLabel, providerLabel } from "@/lib/catalog"
import i18next from "i18next"
import type { SmartField, VoiceCatalogItem } from "@/types/api"

export const smartFieldDescription = (field: SmartField): string => {
  if (field.fieldType === "tts") {
    return i18next.t("smartFields.readsAloud", {
      field: `{{${field.settings.sourceFieldName}}}`,
    })
  }

  return field.settings.promptText
}

/** The model or voice a field runs with, named as its picker names it. On the
 *  free plan, paid-only text settings run as Auto Standard. A field that follows
 *  the defaults carries them as its own settings, so this names the default too. */
export const smartFieldModelLabel = (
  field: SmartField,
  isFree: boolean,
  voices: VoiceCatalogItem[] = [],
): string => {
  if (field.fieldType === "tts") {
    const settings = field.settings
    const voice = voices.find((item) => voiceMatchesSettings(item, settings))
    return `${providerLabel(settings.provider)} · ${voice?.name ?? settings.voiceId}`
  }
  if (field.fieldType === "image") return modelLabel(field.settings.model)

  return chatModelLabel(
    isFree && isPaidOnlyChatSettings(field.settings)
      ? freePlanChatSettings(field.settings)
      : field.settings,
  )
}
