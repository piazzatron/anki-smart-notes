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

/**
 * The UI presents the four GPT Image 2.5 wire models as one "GPT Image 2.5"
 * choice plus two switches: Richer detail (Sunburst) and Max quality (medium).
 */
export interface GptImage25Options {
  richerDetail: boolean
  maxQuality: boolean
}

/** Select value standing in for every GPT Image 2.5 model. */
export const GPT_IMAGE_25 = "gpt-image-2.5"

const GPT_IMAGE_25_MODELS: Record<string, GptImage25Options> = {
  "gpt-image-2.5-flare-low": { richerDetail: false, maxQuality: false },
  "gpt-image-2.5-flare-medium": { richerDetail: false, maxQuality: true },
  "gpt-image-2.5-sunburst-low": { richerDetail: true, maxQuality: false },
  "gpt-image-2.5-sunburst-medium": { richerDetail: true, maxQuality: true },
}

export const gptImage25Options = (model: string): GptImage25Options | null =>
  GPT_IMAGE_25_MODELS[model] ?? null

export const gptImage25Model = (options: GptImage25Options): string => {
  const match = Object.entries(GPT_IMAGE_25_MODELS).find(
    ([, candidate]) =>
      candidate.richerDetail === options.richerDetail &&
      candidate.maxQuality === options.maxQuality,
  )
  if (match === undefined) throw new Error("Unknown GPT Image 2.5 options")
  return match[0]
}

/** Catalog models for the picker, with GPT Image 2.5 collapsed into one entry. */
export const imageModelChoices = (models: CatalogModel[]): CatalogModel[] => {
  const choices: CatalogModel[] = []
  for (const model of models) {
    if (gptImage25Options(model.id) === null) {
      choices.push(model)
    } else if (!choices.some((choice) => choice.id === GPT_IMAGE_25)) {
      choices.push({ id: GPT_IMAGE_25, provider: model.provider })
    }
  }
  return choices
}
