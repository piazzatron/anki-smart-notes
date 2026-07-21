import type { Catalog } from "@/types/api"

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
