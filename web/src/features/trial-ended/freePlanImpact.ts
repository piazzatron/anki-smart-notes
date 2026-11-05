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

import type { ChatGenerationSettings, SmartField } from "@/types/api"

export interface FreePlanImpact {
  /** Voice fields, which stop generating. */
  voiceFields: number
  /** Image fields, which stop generating. */
  imageFields: number
  /** Text fields on a model or level above Auto Standard, which fall back to it. */
  modelFallbacks: number
  /** Text fields with web search on, which run without it. */
  webSearchFallbacks: number
}

/** What the free plan changes about the user's own enabled Smart Fields. A text
 *  field that follows the defaults is judged by the defaults. */
export const getFreePlanImpact = (
  smartFields: SmartField[],
  chatDefaults: ChatGenerationSettings,
): FreePlanImpact => {
  const enabled = smartFields.filter((field) => field.enabled)
  const chatSettings = enabled.flatMap((field) =>
    field.fieldType !== "chat"
      ? []
      : [
          field.settings.usesDefaultGenerationSettings
            ? chatDefaults
            : field.settings,
        ],
  )

  return {
    voiceFields: enabled.filter((field) => field.fieldType === "tts").length,
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
