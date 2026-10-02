import i18next from "i18next"

const MODEL_LABELS: Record<string, string> = {
  "gpt-5-mini": "GPT-5 Mini",
  "gpt-5-chat-latest": "GPT-5 (No Reasoning)",
  "gpt-5": "GPT-5 (Reasoning)",
  "claude-haiku-4-5": "Claude Haiku 4.5",
  "claude-sonnet-4-6": "Claude Sonnet 4.6",
  "claude-opus-4-6": "Claude Opus 4.6",
  "gemini-3.1-flash-lite": "Gemini 3.1 Flash Lite",
  "gemini-3-flash": "Gemini 3 Flash",
  "gemini-3.1-pro": "Gemini 3.1 Pro",
  "gpt-image-2.5-flare-low": "GPT Image 2.5",
  "gpt-image-2.5-flare-medium": "GPT Image 2.5",
  "gpt-image-2.5-sunburst-low": "GPT Image 2.5",
  "gpt-image-2.5-sunburst-medium": "GPT Image 2.5",
  "nano-banana-2": "Nano Banana 2",
  "z-image-turbo": "Z-Image Turbo",
}

const MODEL_COSTS: Record<string, string> = {
  "auto-max": "4",
  "gpt-5-mini": "1",
  "gpt-5-chat-latest": "7++",
  "gpt-5": "7",
  "claude-haiku-4-5": "3",
  "claude-sonnet-4-6": "10",
  "claude-opus-4-6": "16",
  "gemini-3.1-flash-lite": "1",
  "gemini-3-flash": "2",
  "gemini-3.1-pro": "8",
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
  if (model === "auto-max") return i18next.t("common.autoMax")
  return MODEL_LABELS[model] ?? model
}

export const modelCostLabel = (model: string): string | undefined => {
  if (model === "auto") return i18next.t("common.bestValueCost")
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
