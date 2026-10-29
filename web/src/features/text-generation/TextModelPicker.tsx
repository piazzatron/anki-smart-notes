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

import { ChevronDown, ChevronRight } from "lucide-react"
import { useRef, useState, type CSSProperties, type MouseEvent } from "react"
import { Trans, useTranslation } from "react-i18next"

import { BoltIcon, WarningIcon } from "@/components/shared/Icons"
import { Divider } from "@/components/ui/Divider"
import { InfoTip } from "@/components/ui/InfoTip"
import {
  OptionGroup,
  OptionGroupItem,
  OptionList,
  OptionRow,
} from "@/components/ui/OptionList"
import { Pill } from "@/components/ui/Pill"
import { Toggle } from "@/components/ui/Toggle"
import {
  modelCost,
  modelCostLabel,
  modelLabel,
  providerLabel,
} from "@/lib/catalog"
import type { ChatGenerationSettings, ChatModelCatalog } from "@/types/api"

import {
  INTELLIGENCE_LEVELS,
  autoSettingsFor,
  intelligenceLevelOf,
  type IntelligenceLevel,
} from "./intelligence"

interface TextModelPickerProps {
  catalog: ChatModelCatalog
  /** Surfaces hang past the column's left edge by their own padding, so their text lines
   *  up with the heading above. Off where there's no room, as in a dialog. */
  hanging?: boolean
  onChange: (settings: ChatGenerationSettings) => void
  value: ChatGenerationSettings
}

const LEVEL_COLORS: Record<IntelligenceLevel, string> = {
  high: "var(--color-pastel-sky)",
  max: "var(--color-pastel-pink)",
  standard: "var(--color-pastel-mint)",
}

// Expensive models get the caution tint so the jump from Auto is hard to miss.
const EXPENSIVE_MULTIPLIER = 10

/** Auto with its intelligence slider up front; specific models and web search sit under
 *  Advanced options. Shared by the Text defaults screen and the field editor. */
export const TextModelPicker = ({
  catalog,
  hanging = false,
  onChange,
  value,
}: TextModelPickerProps) => {
  const { t } = useTranslation()
  const isAuto = value.provider === "auto"
  // Open from the start when something in it is already in use, so nothing is hidden.
  const [advancedOpen, setAdvancedOpen] = useState(
    !isAuto || value.webSearchEnabled,
  )
  const surface = `rounded-xl bg-white/[0.05] ${hanging ? "hang" : "px-hang"}`

  return (
    <div>
      {isAuto ? (
        <div className={`${surface} pt-6 pb-[26px]`}>
          <div className="flex items-center gap-2">
            <BoltIcon className="text-pastel-lavender" size={16} />
            <span className="text-[14.5px] font-bold text-ink">
              {t("intelligence.autoName")}
            </span>
          </div>
          <p className="mt-1 text-xs leading-4 text-ink-muted">
            {t("intelligence.autoDescription")}
          </p>
          <Divider className="my-5" />
          <div className="mb-4 flex items-center gap-1.5">
            <span className="text-[13px] font-semibold text-ink-muted">
              {t("intelligence.label")}
            </span>
            <InfoTip label={t("intelligence.tipLabel")}>
              <p>{t("intelligence.tipIntro")}</p>
              <ul className="mt-2 list-disc space-y-1 ps-4">
                {INTELLIGENCE_LEVELS.map(({ id }) => (
                  <li key={id}>
                    <Trans
                      components={{ level: <b className="font-bold" /> }}
                      i18nKey={`intelligence.tips.${id}`}
                    />
                  </li>
                ))}
              </ul>
            </InfoTip>
          </div>
          <IntelligenceSlider
            level={intelligenceLevelOf(value)}
            onChange={(level) =>
              onChange({ ...value, ...autoSettingsFor(level) })
            }
          />
        </div>
      ) : (
        <div className={`${surface} py-5`}>
          <div className="flex items-center gap-2">
            <span className="min-w-0 flex-1 truncate text-[14.5px] font-bold text-ink">
              {modelLabel(value.model)}
            </span>
            <CostPill model={value.model} />
          </div>
          <p className="mt-1 text-xs leading-4 text-ink-muted">
            {providerLabel(value.provider)}
          </p>
        </div>
      )}

      <button
        aria-expanded={advancedOpen}
        className="mt-5 inline-flex cursor-pointer items-center gap-1 py-1 text-[13px] font-medium text-ink-muted transition hover:text-ink"
        onClick={() => setAdvancedOpen(!advancedOpen)}
        type="button"
      >
        {t("intelligence.advancedOptions")}
        <ChevronDown
          aria-hidden
          className={`size-3.5 transition-transform ${advancedOpen ? "rotate-180" : ""}`}
        />
      </button>

      {advancedOpen && (
        <div className="mt-3 grid gap-3">
          <SpecificModelList
            catalog={catalog}
            className={hanging ? "-mx-hang" : ""}
            onChange={onChange}
            value={value}
          />
          <div className={`${surface} flex items-center gap-4 py-[18px]`}>
            <div className="min-w-0 flex-1">
              <p className="flex min-h-[22px] items-center gap-2 text-sm font-medium text-ink">
                {t("intelligence.webSearch")}
                <Pill tone="warning">{t("intelligence.veryHighCost")}</Pill>
              </p>
              <p className="mt-1.5 text-xs leading-4 text-ink-muted">
                {t("intelligence.webSearchDescription")}
              </p>
            </div>
            <Toggle
              aria-label={t("intelligence.webSearch")}
              checked={value.webSearchEnabled}
              onCheckedChange={(webSearchEnabled) =>
                onChange({ ...value, webSearchEnabled })
              }
            />
          </div>
        </div>
      )}
    </div>
  )
}

// Three stops on a track that fills with the levels' colors. The fill animates by
// clipping one full-width gradient, so each level keeps its color as it fills.
const IntelligenceSlider = ({
  level,
  onChange,
}: {
  level: IntelligenceLevel
  onChange: (level: IntelligenceLevel) => void
}) => {
  const { t } = useTranslation()
  const stopRefs = useRef<(HTMLButtonElement | null)[]>([])
  const index = INTELLIGENCE_LEVELS.findIndex((item) => item.id === level)
  const step = 100 / (INTELLIGENCE_LEVELS.length - 1)

  return (
    <div>
      <OptionGroup
        aria-label={t("intelligence.label")}
        className="relative mx-[9px] h-1.5 rounded-full bg-white/[0.08]"
        loop={false}
        onValueChange={(id) => {
          const next = INTELLIGENCE_LEVELS.find((item) => item.id === id)
          if (next !== undefined) onChange(next.id)
        }}
        value={level}
      >
        <div
          className="absolute inset-0 rounded-full bg-[linear-gradient(90deg,var(--color-pastel-mint),var(--color-pastel-sky)_50%,var(--color-pastel-pink))] transition-[clip-path] duration-[450ms] ease-[cubic-bezier(0.22,1,0.36,1)] motion-reduce:transition-none rtl:-scale-x-100"
          style={{
            clipPath: `inset(0 ${100 - index * step}% 0 0 round 3px)`,
          }}
        />
        <div className="absolute -inset-x-[9px] -top-1.5 flex justify-between">
          {INTELLIGENCE_LEVELS.map((item, itemIndex) => (
            <OptionGroupItem
              aria-label={`${t(`intelligence.levels.${item.id}`)}, ${t("common.multiplierCost", { multiplier: item.cost })}`}
              className={`grid size-[18px] cursor-pointer place-items-center rounded-full transition-transform ${
                itemIndex === index
                  ? "animate-stop-pop bg-[var(--level)]"
                  : "bg-zinc-800"
              }`}
              key={item.id}
              ref={(element) => {
                stopRefs.current[itemIndex] = element
              }}
              style={{ "--level": LEVEL_COLORS[item.id] } as CSSProperties}
              value={item.id}
            >
              <span
                className={`rounded-full ${
                  itemIndex === index
                    ? "size-1.5 bg-panel-raised"
                    : `size-2 bg-[var(--level)] ${itemIndex < index ? "" : "opacity-50"}`
                }`}
              />
            </OptionGroupItem>
          ))}
        </div>
      </OptionGroup>
      {/* The labels repeat the stops for the mouse; the stops carry the names for
          keyboards and screen readers. A click moves focus to the matching stop, so the
          arrow keys carry on from there. */}
      <div aria-hidden className="mt-3.5 grid grid-cols-3">
        {INTELLIGENCE_LEVELS.map((item, itemIndex) => (
          <button
            className={`grid cursor-pointer gap-0.5 text-[13px] first:justify-items-start last:justify-items-end [&:nth-child(2)]:justify-items-center ${
              itemIndex === index ? "" : "text-ink-muted"
            }`}
            key={item.id}
            onClick={() => {
              onChange(item.id)
              stopRefs.current[itemIndex]?.focus()
            }}
            onMouseDown={(event) => event.preventDefault()}
            style={
              itemIndex === index ? { color: LEVEL_COLORS[item.id] } : undefined
            }
            tabIndex={-1}
            type="button"
          >
            <span className="font-semibold">
              {t(`intelligence.levels.${item.id}`)}
            </span>
            <span
              className={`text-xs tabular-nums ${itemIndex === index ? "text-ink" : "text-ink-muted"}`}
            >
              {t("common.multiplierCost", { multiplier: item.cost })}
            </span>
          </button>
        ))}
      </div>
    </div>
  )
}

// The other models, in a list that opens in place: provider groups, a row per model with
// its cost. Clicking one closes the list and the card above shows it; arrow keys move
// through the rows without closing it, and Enter closes it.
const SpecificModelList = ({
  catalog,
  className,
  onChange,
  value,
}: {
  catalog: ChatModelCatalog
  className: string
  onChange: (settings: ChatGenerationSettings) => void
  value: ChatGenerationSettings
}) => {
  const { t } = useTranslation()
  const [open, setOpen] = useState(false)
  const isAuto = value.provider === "auto"
  const levels = INTELLIGENCE_LEVELS.map((item) => item.cost)
  const closeOnPointerClick = (event: MouseEvent) => {
    if (event.detail > 0) setOpen(false)
  }

  return (
    <div className={`overflow-hidden rounded-xl bg-white/[0.05] ${className}`}>
      <button
        aria-expanded={open}
        className="flex w-full cursor-pointer items-center gap-2.5 px-hang py-[18px] text-start text-sm font-medium text-ink transition hover:bg-white/[0.02]"
        onClick={() => setOpen(!open)}
        type="button"
      >
        <span className="shrink-0">{t("intelligence.specificModel")}</span>
        <span className="min-w-0 flex-1 truncate text-end font-normal text-ink-muted">
          {isAuto ? "" : modelLabel(value.model)}
        </span>
        <ChevronRight
          aria-hidden
          className={`size-3.5 shrink-0 text-ink-faint transition-transform rtl:rotate-180 ${open ? "rotate-90 rtl:rotate-90" : ""}`}
        />
      </button>
      {open && (
        <OptionList
          className="pb-1.5"
          label={t("intelligence.specificModel")}
          onKeyDown={(event) => {
            if (event.key === "Enter") setOpen(false)
          }}
          onValueChange={(id) => {
            // The Auto row's value is the catalog's own "auto" entry. Coming back to
            // Auto starts at Standard, whatever level Auto last had.
            if (id === "auto") {
              onChange({ ...value, ...autoSettingsFor("standard") })
              return
            }
            const model = catalog.models.find((item) => item.id === id)
            if (model !== undefined)
              onChange({ ...value, model: model.id, provider: model.provider })
          }}
          value={isAuto ? "auto" : value.model}
        >
          <p className="flex items-center gap-1.5 px-hang pb-1.5 text-xs leading-4 text-caution-soft">
            <WarningIcon size={14} />
            {t("intelligence.specificModelWarning")}
          </p>
          <OptionRow
            className="px-hang py-3"
            label={t("intelligence.autoName")}
            onClick={closeOnPointerClick}
            trailing={
              <Pill>
                {t("intelligence.autoCostRange", {
                  max: Math.max(...levels),
                  min: Math.min(...levels),
                })}
              </Pill>
            }
            value="auto"
          />
          {catalog.providers
            .filter((provider) => provider !== "auto")
            .map((provider) => (
              <div key={provider}>
                <p className="px-hang pt-3 pb-1.5 text-[11px] font-semibold tracking-[0.055em] text-ink-muted uppercase">
                  {providerLabel(provider)}
                </p>
                {catalog.models
                  .filter((model) => model.provider === provider)
                  .map((model) => (
                    <OptionRow
                      className="px-hang py-3"
                      key={model.id}
                      label={modelLabel(model.id)}
                      onClick={closeOnPointerClick}
                      trailing={<CostPill model={model.id} />}
                      value={model.id}
                    />
                  ))}
              </div>
            ))}
        </OptionList>
      )}
    </div>
  )
}

const CostPill = ({ model }: { model: string }) => {
  const cost = modelCost(model)
  if (cost === undefined) return null
  return (
    <Pill tone={cost >= EXPENSIVE_MULTIPLIER ? "caution" : "neutral"}>
      {modelCostLabel(model)}
    </Pill>
  )
}
