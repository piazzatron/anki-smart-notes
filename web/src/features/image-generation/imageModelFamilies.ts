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

import type { CatalogModel } from "@/types/api"

export type ImageModelSwitch = "richerDetail" | "maxQuality" | "extraReasoning"
type SwitchStates = Partial<Record<ImageModelSwitch, boolean>>

/**
 * One picker choice standing for several wire models, told apart by switches. The
 * variant with every switch off is the family's default.
 */
export interface ImageModelFamily {
  // Select value for the whole family.
  id: string
  label: string
  switches: ImageModelSwitch[]
  variants: Record<string, SwitchStates>
  // One line per setting for the "which models run" tip.
  underTheHood: string[]
}

export const IMAGE_MODEL_FAMILIES: readonly ImageModelFamily[] = [
  {
    id: "gpt-image-2.5",
    label: "imageGeneration.gptImage25",
    switches: ["richerDetail", "maxQuality"],
    variants: {
      "gpt-image-2.5-flare-low": {},
      "gpt-image-2.5-flare-medium": { maxQuality: true },
      "gpt-image-2.5-sunburst-low": { richerDetail: true },
      "gpt-image-2.5-sunburst-medium": { richerDetail: true, maxQuality: true },
    },
    underTheHood: [
      "imageGeneration.underTheHood.gptStandard",
      "imageGeneration.underTheHood.gptRicherDetail",
      "imageGeneration.underTheHood.gptMaxQuality",
    ],
  },
  {
    id: "nano-banana",
    label: "imageGeneration.nanoBanana",
    switches: ["extraReasoning"],
    variants: {
      "nano-banana-2-lite": {},
      "nano-banana-2": { extraReasoning: true },
    },
    underTheHood: [
      "imageGeneration.underTheHood.nanoStandard",
      "imageGeneration.underTheHood.nanoExtraReasoning",
    ],
  },
]

/** Label, description, and cost pill for each switch (i18n keys). */
export const IMAGE_MODEL_SWITCHES: Record<
  ImageModelSwitch,
  { label: string; description: string; cost: string | null }
> = {
  richerDetail: {
    label: "imageGeneration.richerDetail",
    description: "imageGeneration.richerDetailDescription",
    cost: null,
  },
  maxQuality: {
    label: "imageGeneration.maxQuality",
    description: "imageGeneration.maxQualityDescription",
    cost: "imageGeneration.doubleCost",
  },
  extraReasoning: {
    label: "imageGeneration.extraReasoning",
    description: "imageGeneration.extraReasoningDescription",
    cost: "imageGeneration.extraReasoningCost",
  },
}

export const getImageModelFamily = (model: string): ImageModelFamily | null =>
  IMAGE_MODEL_FAMILIES.find(
    (family) => family.id === model || model in family.variants,
  ) ?? null

/** Whether a switch is on for one of the family's wire models. */
export const isSwitchOn = (
  family: ImageModelFamily,
  model: string,
  key: ImageModelSwitch,
): boolean => family.variants[model]?.[key] ?? false

/** The wire model a set of switch states selects; missing switches are off. */
export const familyModel = (
  family: ImageModelFamily,
  states: SwitchStates,
): string => {
  const match = Object.entries(family.variants).find(([, variant]) =>
    family.switches.every(
      (key) => (variant[key] ?? false) === (states[key] ?? false),
    ),
  )
  if (match === undefined) throw new Error(`Unknown ${family.id} switches`)
  return match[0]
}

/** Catalog models for the picker, with each family collapsed into one entry. */
export const imageModelChoices = (models: CatalogModel[]): CatalogModel[] => {
  const choices: CatalogModel[] = []
  for (const model of models) {
    const family = getImageModelFamily(model.id)
    if (family === null) {
      choices.push(model)
    } else if (!choices.some((choice) => choice.id === family.id)) {
      choices.push({ id: family.id, provider: model.provider })
    }
  }
  return choices
}
