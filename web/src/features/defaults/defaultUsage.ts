import type { SmartField } from "@/types/api"

export const getDefaultUsage = (
  smartFields: SmartField[],
  fieldType: SmartField["fieldType"],
) => {
  const matchingFields = smartFields.filter(
    (field) => field.fieldType === fieldType,
  )

  return {
    following: matchingFields.filter(
      (field) => field.settings.usesDefaultGenerationSettings,
    ).length,
    pinned: matchingFields.filter(
      (field) => !field.settings.usesDefaultGenerationSettings,
    ).length,
  }
}
