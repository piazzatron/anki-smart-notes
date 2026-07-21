import type { Catalog, SmartField } from "@/types/api"

export const getTextDefaultUsage = (smartFields: SmartField[]) => {
  const textFields = smartFields.filter((field) => field.fieldType === "chat")

  return {
    following: textFields.filter(
      (field) => field.settings.usesDefaultGenerationSettings,
    ).length,
    pinned: textFields.filter(
      (field) => !field.settings.usesDefaultGenerationSettings,
    ).length,
  }
}

export const getProviderForModel = (
  catalog: Catalog,
  model: string,
): string => {
  const provider = catalog.chat.models.find(
    (item) => item.id === model,
  )?.provider
  if (provider === undefined) {
    throw new Error(`Chat catalog is missing model ${model}`)
  }

  return provider
}
