import i18next from "i18next"

import { modelLabel } from "@/lib/catalog"
import type { ChatGenerationSettings } from "@/types/api"

export type IntelligenceLevel = "standard" | "high" | "max"

/** Auto's levels, cheapest first. Cost is relative to Standard, from the pricing sheet's
 *  "Cost vs Auto Standard" column (pricing/text.csv), rounded. */
export const INTELLIGENCE_LEVELS: { cost: number; id: IntelligenceLevel }[] = [
  { cost: 1, id: "standard" },
  { cost: 3, id: "high" },
  { cost: 12, id: "max" },
]

type AutoSettings = Pick<
  ChatGenerationSettings,
  "model" | "provider" | "reasoningLevel"
>

// Auto's level is its reasoning level: off (or the older low) is Standard, high is
// High, and max is Max (`autoModelsMap` in server/src/models/models.ts).
const REASONING_LEVEL_FOR: Record<IntelligenceLevel, string> = {
  standard: "off",
  high: "high",
  max: "max",
}

export const intelligenceLevelOf = (
  settings: Pick<ChatGenerationSettings, "reasoningLevel">,
): IntelligenceLevel => {
  if (settings.reasoningLevel === "max") return "max"
  return settings.reasoningLevel === "high" ? "high" : "standard"
}

export const autoSettingsFor = (level: IntelligenceLevel): AutoSettings => ({
  model: "auto",
  provider: "auto",
  reasoningLevel: REASONING_LEVEL_FOR[level],
})

/** A chat model as one short label: "Auto · High" for Auto, the model name otherwise. */
export const chatModelLabel = (
  settings: Pick<
    ChatGenerationSettings,
    "model" | "provider" | "reasoningLevel"
  >,
): string =>
  settings.provider === "auto"
    ? i18next.t("intelligence.autoWithLevel", {
        level: i18next.t(
          `intelligence.levels.${intelligenceLevelOf(settings)}`,
        ),
      })
    : modelLabel(settings.model)
