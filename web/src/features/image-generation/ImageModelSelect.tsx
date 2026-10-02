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

import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/Select"
import { Toggle } from "@/components/ui/Toggle"
import { useTranslation } from "react-i18next"
import { modelLabel } from "@/lib/catalog"
import i18next from "@/lib/i18n"
import type { ImageGenerationSettings, ImageModelCatalog } from "@/types/api"
import {
  GPT_IMAGE_25,
  type GptImage25Options,
  gptImage25Model,
  gptImage25Options,
  imageModelChoices,
} from "./gptImage25"

interface ImageModelSelectProps {
  ariaLabel?: string
  catalog: ImageModelCatalog
  id?: string
  onValueChange: (settings: ImageGenerationSettings) => void
  value: string
}

export const ImageModelSelect = ({
  ariaLabel,
  catalog,
  id,
  onValueChange,
  value,
}: ImageModelSelectProps) => {
  const { t } = useTranslation()
  const options = gptImage25Options(value)

  const selectModel = (model: string) => {
    const selected = catalog.models.find((item) => item.id === model)
    if (selected === undefined) {
      throw new Error(i18next.t("defaults.errors.missingImageModel", { model }))
    }
    onValueChange({ model, provider: selected.provider })
  }

  const setOption = (change: Partial<GptImage25Options>) => {
    if (options === null) return
    selectModel(gptImage25Model({ ...options, ...change }))
  }

  const extras = [
    {
      key: "richerDetail",
      label: t("imageGeneration.richerDetail"),
      description: t("imageGeneration.richerDetailDescription"),
      cost: t("imageGeneration.noExtraCost"),
      premium: false,
    },
    {
      key: "maxQuality",
      label: t("imageGeneration.maxQuality"),
      description: t("imageGeneration.maxQualityDescription"),
      cost: t("imageGeneration.doubleCost"),
      premium: true,
    },
  ] as const

  return (
    <>
      <Select
        onValueChange={(choice) =>
          selectModel(
            choice === GPT_IMAGE_25
              ? gptImage25Model({ richerDetail: false, maxQuality: false })
              : choice,
          )
        }
        value={options === null ? value : GPT_IMAGE_25}
      >
        <SelectTrigger aria-label={ariaLabel} id={id}>
          <SelectValue />
        </SelectTrigger>
        <SelectContent>
          {imageModelChoices(catalog.models).map((model) => (
            <SelectItem key={`${model.provider}:${model.id}`} value={model.id}>
              <span className="min-w-0 flex-1 truncate font-semibold text-zinc-100">
                {model.id === GPT_IMAGE_25
                  ? t("imageGeneration.gptImage25")
                  : modelLabel(model.id)}
              </span>
            </SelectItem>
          ))}
        </SelectContent>
      </Select>

      {/* Plain GPT Image 2.5 is the default; extras are opt-in switches that pick
          the underlying model, so users never see Flare vs Sunburst. */}
      {options !== null && (
        <div className="mt-4">
          <p className="mb-1 text-[10px] font-semibold tracking-[0.08em] text-ink-faint uppercase">
            {t("imageGeneration.extras")}
          </p>
          {extras.map((extra, index) => (
            <div
              className={`flex items-start gap-4 py-2.5 ${index > 0 ? "border-t border-white/[0.065]" : ""}`}
              key={extra.key}
            >
              <div className="min-w-0 flex-1">
                <p className="flex items-center gap-2 text-xs font-semibold text-zinc-200">
                  {extra.label}
                  <span
                    className={`rounded px-1.5 py-px text-[10px] font-semibold whitespace-nowrap ${
                      extra.premium
                        ? "bg-indigo/14 text-indigo-soft"
                        : "bg-white/[0.06] text-ink-muted"
                    }`}
                  >
                    {extra.cost}
                  </span>
                </p>
                <p className="mt-1 text-[11px] leading-4 text-ink-muted">
                  {extra.description}
                </p>
              </div>
              <div className="mt-0.5">
                <Toggle
                  aria-label={extra.label}
                  checked={options[extra.key]}
                  onCheckedChange={(checked) =>
                    setOption({ [extra.key]: checked })
                  }
                />
              </div>
            </div>
          ))}
        </div>
      )}
    </>
  )
}
