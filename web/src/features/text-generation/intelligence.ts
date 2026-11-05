import i18next from "i18next"

import { modelLabel } from "@/lib/catalog"
import type { ChatGenerationSettings } from "@/types/api"

export type IntelligenceLevel = "standard" | "high" | "max"

/** Auto's levels, cheapest first. Cost is relative to Standard, from the "× Auto" column
 *  of specs/pricing.md, rounded per the ui-design skill. */
export const INTELLIGENCE_LEVELS: { cost: number; id: IntelligenceLevel }[] = [
  { cost: 1, id: "standard" },
  { cost: 2, id: "high" },
  { cost: 8, id: "max" },
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

/** Whether two chat settings read the same in the picker: Auto by its intelligence level
 *  (off and the older low are both Standard), and a specific model by name, ignoring
 *  the reasoning level only Auto reads. */
export const chatSettingsMatch = (
  a: ChatGenerationSettings,
  b: ChatGenerationSettings,
): boolean =>
  a.provider === b.provider &&
  a.model === b.model &&
  a.webSearchEnabled === b.webSearchEnabled &&
  a.stripHtml === b.stripHtml &&
  (a.provider !== "auto" || intelligenceLevelOf(a) === intelligenceLevelOf(b))

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

/** Text settings the free plan pauses: any model or level but Auto Standard, or
 *  web search. They stay saved and come back on a paid plan. */
export const isPaidOnlyChatSettings = (
  settings: Pick<
    ChatGenerationSettings,
    "model" | "reasoningLevel" | "webSearchEnabled"
  >,
) =>
  settings.model !== "auto" ||
  intelligenceLevelOf(settings) !== "standard" ||
  settings.webSearchEnabled

/** What paused text settings run as on the free plan: Auto Standard, no search. */
export const freePlanChatSettings = <Settings extends AutoSettingsInput>(
  settings: Settings,
): Settings => ({
  ...settings,
  ...autoSettingsFor("standard"),
  webSearchEnabled: false,
})

type AutoSettingsInput = Pick<
  ChatGenerationSettings,
  "model" | "provider" | "reasoningLevel" | "webSearchEnabled"
>
