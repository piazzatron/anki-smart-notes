/*
 * Copyright (C) 2024 Michael Piazza
 *
 * This file is part of Smart Notes.
 *
 * Smart Notes is free software: you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation, either version 3 of the License, or
 * (at your option) any later version.
 *
 * Smart Notes is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with Smart Notes. If not, see <https://www.gnu.org/licenses/>.
 */

import { planVoice } from "@/features/defaults/voiceDefaults"
import type {
  GenerationDefaults,
  SmartField,
  VoiceCatalogItem,
  VoiceRule,
} from "@/types/api"

export interface FreePlanImpact {
  /** Voice fields with no free voice in their language, which stop generating. */
  voiceStops: number
  /** Voice fields on a voice Free doesn't include, which read with a free one. */
  voiceFallbacks: number
  /** Image fields, which stop generating. */
  imageFields: number
  /** Text fields on a model or level above Auto Standard, which fall back to it. */
  modelFallbacks: number
  /** Text fields with web search on, which run without it. */
  webSearchFallbacks: number
}

interface FreePlanImpactArgs {
  smartFields: SmartField[]
  defaults: Pick<GenerationDefaults, "chat" | "tts">
  /** The voices the free plan allows, from the server. */
  allowedVoices: VoiceRule[] | null
  /** The voice catalog, or null while it loads, when voice fields count as
   *  unchanged. */
  voices: VoiceCatalogItem[] | null
}

/** What the free plan changes about the user's own enabled Smart Fields. A field
 *  that follows the defaults is judged by the defaults. */
export const getFreePlanImpact = ({
  smartFields,
  defaults,
  allowedVoices,
  voices,
}: FreePlanImpactArgs): FreePlanImpact => {
  const enabled = smartFields.filter((field) => field.enabled)
  const chatSettings = enabled.flatMap((field) =>
    field.fieldType !== "chat"
      ? []
      : [
          field.settings.usesDefaultGenerationSettings
            ? defaults.chat
            : field.settings,
        ],
  )
  const voiceChanges = enabled.flatMap((field) => {
    if (field.fieldType !== "tts" || voices === null) return []
    const saved = field.settings.usesDefaultGenerationSettings
      ? defaults.tts
      : field.settings
    const voice = planVoice(saved, voices, allowedVoices)
    if (voice === null) return ["stops"]
    return voice === saved ? [] : ["fallsBack"]
  })

  return {
    voiceStops: voiceChanges.filter((change) => change === "stops").length,
    voiceFallbacks: voiceChanges.filter((change) => change === "fallsBack")
      .length,
    imageFields: enabled.filter((field) => field.fieldType === "image").length,
    modelFallbacks: chatSettings.filter(
      (settings) =>
        settings.model !== "auto" ||
        settings.reasoningLevel === "high" ||
        settings.reasoningLevel === "max",
    ).length,
    webSearchFallbacks: chatSettings.filter(
      (settings) => settings.webSearchEnabled,
    ).length,
  }
}
