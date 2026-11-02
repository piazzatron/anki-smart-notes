import i18next from "i18next"

const MODEL_LABELS: Record<string, string> = {
  "gpt-6-luna": "GPT-6 Luna",
  "gpt-6.1-terra": "GPT-6.1 Terra",
  "gpt-6.1-sol": "GPT-6.1 Sol",
  "claude-haiku-5-5": "Claude Haiku 5.5",
  "claude-sonnet-5-5": "Claude Sonnet 5.5",
  "claude-opus-5-5": "Claude Opus 5.5",
  "gemini-3.5-flash-lite": "Gemini 3.5 Flash-Lite",
  "gemini-3.8-flash": "Gemini 3.8 Flash",
  "gemini-4-argon": "Gemini 4 Argon",
  "gpt-image-2.5-flare-low": "GPT Image 2.5",
  "gpt-image-2.5-flare-medium": "GPT Image 2.5",
  "gpt-image-2.5-sunburst-low": "GPT Image 2.5",
  "gpt-image-2.5-sunburst-medium": "GPT Image 2.5",
  "nano-banana-2-lite": "Nano Banana (Google)",
  "nano-banana-2.1": "Nano Banana (Google)",
  "z-image-turbo": "Z-Image Turbo",
}

const MODEL_COSTS: Record<string, number> = {
  // Text, relative to Auto at Standard: the "× Auto" column of specs/pricing.md,
  // rounded per the ui-design skill.
  "gpt-6-luna": 0.5,
  "gpt-6.1-terra": 4,
  "gpt-6.1-sol": 15,
  "claude-haiku-5-5": 0.5,
  "claude-sonnet-5-5": 20,
  "claude-opus-5-5": 30,
  "gemini-3.5-flash-lite": 1,
  "gemini-3.8-flash": 5,
  "gemini-4-argon": 15,
  // Images, relative to plain GPT Image 2.5 (~$0.011 billed per image, specs/pricing.md).
  "gpt-image-2.5": 1,
  "nano-banana": 4,
  "z-image-turbo": 0.25,
}

const PROVIDER_LABELS: Record<string, string> = {
  openai: "OpenAI",
  anthropic: "Anthropic",
  google: "Google",
  elevenLabs: "ElevenLabs",
  azure: "Azure",
  voicevox: "VOICEVOX",
}

export const modelLabel = (model: string): string => {
  if (model === "auto") return i18next.t("common.auto")
  return MODEL_LABELS[model] ?? model
}

/** A model's cost as a multiple of its baseline (Auto at Standard for text). */
export const modelCost = (model: string): number | undefined =>
  MODEL_COSTS[model]

export const modelCostLabel = (model: string): string | undefined => {
  const multiplier = MODEL_COSTS[model]
  return multiplier === undefined
    ? undefined
    : i18next.t("common.multiplierCost", { multiplier })
}

export const providerLabel = (provider: string): string => {
  if (provider === "auto") return i18next.t("common.auto")
  if (provider === "replicate") return i18next.t("common.other")
  return PROVIDER_LABELS[provider] ?? provider
}
