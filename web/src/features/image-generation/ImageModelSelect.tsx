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
} from "@/components/ui/Select"
import { InfoTip } from "@/components/ui/InfoTip"
import { Pill } from "@/components/ui/Pill"
import { Toggle } from "@/components/ui/Toggle"
import { useTranslation } from "react-i18next"
import { modelCostLabel, modelLabel } from "@/lib/catalog"
import i18next from "@/lib/i18n"
import type { ImageGenerationSettings, ImageModelCatalog } from "@/types/api"
import {
  IMAGE_MODEL_FAMILIES,
  IMAGE_MODEL_SWITCHES,
  type ImageModelSwitch,
  familyModel,
  getImageModelFamily,
  imageModelChoices,
  isSwitchOn,
} from "./imageModelFamilies"

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
  const family = getImageModelFamily(value)

  const selectModel = (model: string) => {
    const selected = catalog.models.find((item) => item.id === model)
    if (selected === undefined) {
      throw new Error(i18next.t("defaults.errors.missingImageModel", { model }))
    }
    onValueChange({ model, provider: selected.provider })
  }

  const setSwitch = (key: ImageModelSwitch, checked: boolean) => {
    if (family === null) return
    const states = Object.fromEntries(
      family.switches.map((other) => [other, isSwitchOn(family, value, other)]),
    )
    selectModel(familyModel(family, { ...states, [key]: checked }))
  }

  return (
    <>
      <Select
        onValueChange={(choice) => {
          const chosenFamily = IMAGE_MODEL_FAMILIES.find(
            (candidate) => candidate.id === choice,
          )
          selectModel(
            chosenFamily === undefined ? choice : familyModel(chosenFamily, {}),
          )
        }}
        value={family?.id ?? value}
      >
        <SelectTrigger aria-label={ariaLabel} id={id}>
          <ImageModelOption modelId={family?.id ?? value} />
        </SelectTrigger>
        <SelectContent>
          {imageModelChoices(catalog.models).map((model) => (
            <SelectItem key={`${model.provider}:${model.id}`} value={model.id}>
              <ImageModelOption modelId={model.id} />
            </SelectItem>
          ))}
        </SelectContent>
      </Select>

      {/* A family's default is its plain model; switches are opt-in and pick the
          underlying model, which the ⓘ names for anyone curious. */}
      {family !== null && (
        <div className="mt-4">
          <p className="mb-1 flex items-center gap-1.5 text-[10px] font-semibold tracking-[0.08em] text-ink-faint uppercase">
            {t("imageGeneration.extraSettings")}
            <InfoTip label={t("imageGeneration.underTheHoodLabel")}>
              <ul className="space-y-1">
                {family.underTheHood.map((line) => (
                  <li key={line}>{t(line)}</li>
                ))}
              </ul>
            </InfoTip>
          </p>
          {family.switches.map((key, index) => {
            const { cost, description, label } = IMAGE_MODEL_SWITCHES[key]
            return (
              <div
                className={`flex items-start gap-4 py-2.5 ${index > 0 ? "border-t border-white/[0.065]" : ""}`}
                key={key}
              >
                <div className="min-w-0 flex-1">
                  <p className="flex items-center gap-2 text-xs font-semibold text-zinc-200">
                    {t(label)}
                    {cost !== null && <Pill tone="warning">{t(cost)}</Pill>}
                  </p>
                  <p className="mt-1 text-[11px] leading-4 text-ink-muted">
                    {t(description)}
                  </p>
                </div>
                <div className="mt-0.5">
                  <Toggle
                    aria-label={t(label)}
                    checked={isSwitchOn(family, value, key)}
                    onCheckedChange={(checked) => setSwitch(key, checked)}
                  />
                </div>
              </div>
            )
          })}
        </div>
      )}
    </>
  )
}

// The model's (or family's) name with its cost relative to plain GPT Image 2.5, as the
// text model picker shows it.
const ImageModelOption = ({ modelId }: { modelId: string }) => {
  const { t } = useTranslation()
  const costLabel = modelCostLabel(modelId)
  const family = IMAGE_MODEL_FAMILIES.find(
    (candidate) => candidate.id === modelId,
  )

  return (
    <span className="flex min-w-0 items-center gap-2">
      <span className="min-w-0 flex-1 truncate font-semibold text-zinc-100">
        {family === undefined ? modelLabel(modelId) : t(family.label)}
      </span>
      {costLabel !== undefined && <Pill>{costLabel}</Pill>}
    </span>
  )
}
