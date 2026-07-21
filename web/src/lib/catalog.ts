const MODEL_LABELS: Record<string, string> = {
  auto: "Auto",
  "auto-max": "Auto MAX",
  "gpt-5-mini": "GPT-5 Mini",
  "gpt-5-chat-latest": "GPT-5 (No Reasoning)",
  "gpt-5": "GPT-5 (Reasoning)",
  "claude-haiku-4-5": "Claude Haiku 4.5",
  "claude-sonnet-4-6": "Claude Sonnet 4.6",
  "claude-opus-4-6": "Claude Opus 4.6",
  "gemini-3.1-flash-lite": "Gemini 3.1 Flash Lite",
  "gemini-3-flash": "Gemini 3 Flash",
  "gemini-3.1-pro": "Gemini 3.1 Pro",
  "gpt-image-1.5-low": "GPT Image 1.5 Low",
  "gpt-image-1.5-medium": "GPT Image 1.5 Medium",
  "gpt-image-2-low": "GPT Image 2 Low",
  "gpt-image-2-medium": "GPT Image 2 Medium",
  "nano-banana-2": "Nano Banana 2",
  "z-image-turbo": "Z-Image Turbo",
  "flux-dev": "Flux Dev",
}

const MODEL_COSTS: Record<string, string> = {
  auto: "Best Value, 0.3× cost",
  "auto-max": "4× cost",
  "gpt-5-mini": "1× cost",
  "gpt-5-chat-latest": "7×++ cost",
  "gpt-5": "7× cost",
  "claude-haiku-4-5": "3× cost",
  "claude-sonnet-4-6": "10× cost",
  "claude-opus-4-6": "16× cost",
  "gemini-3.1-flash-lite": "1× cost",
  "gemini-3-flash": "2× cost",
  "gemini-3.1-pro": "8× cost",
}

const PROVIDER_LABELS: Record<string, string> = {
  auto: "Auto",
  openai: "OpenAI",
  anthropic: "Anthropic",
  google: "Google",
  elevenLabs: "ElevenLabs",
  azure: "Azure",
  voicevox: "VOICEVOX",
  replicate: "Other",
}

export const modelLabel = (model: string): string =>
  MODEL_LABELS[model] ?? model

export const modelCostLabel = (model: string): string | undefined =>
  MODEL_COSTS[model]

export const providerLabel = (provider: string): string =>
  PROVIDER_LABELS[provider] ?? provider
