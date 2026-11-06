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

import { useMemo, useState, type ReactNode } from "react"
import { useTranslation } from "react-i18next"

import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/Select"
import { OptionList, OptionRow } from "@/components/ui/OptionList"
import { Pill } from "@/components/ui/Pill"
import { FieldLabel } from "@/components/ui/FieldLabel"
import { SearchIcon } from "@/components/shared/Icons"
import {
  openUpgradeSheet,
  UpgradeLockIcon,
} from "@/components/shared/UpgradeSheet"
import { providerLabel } from "@/lib/catalog"
import type { TTSGenerationSettings, VoiceCatalog } from "@/types/api"

import { useAllowedVoices } from "./useVoiceCatalog"
import {
  filterVoices,
  isVoiceAllowed,
  shownVoice,
  voiceKey,
  voiceMatchesSettings,
} from "./voiceDefaults"

const VOICE_GENDER_OPTIONS = ["All", "Female", "Male"]
interface VoicePickerProps {
  catalog: VoiceCatalog
  children?: ReactNode
  layout?: "columns" | "stacked"
  listHeight?: number
  listMaxHeight?: number
  onSelect: (settings: TTSGenerationSettings) => void
  value: TTSGenerationSettings
}

export const VoicePicker = ({
  catalog,
  children,
  layout = "stacked",
  listHeight,
  listMaxHeight,
  onSelect,
  value,
}: VoicePickerProps) => {
  const { i18n, t } = useTranslation()
  // On a plan that limits voices, the others are locked, and a saved voice it
  // doesn't include shows the free voice that stands in for it.
  const allowedVoices = useAllowedVoices()
  const shown = shownVoice(value, catalog.voices, allowedVoices)
  const selectedVoice = catalog.voices.find((voice) =>
    voiceMatchesSettings(voice, shown),
  )
  const [filters, setFilters] = useState({
    gender: "All",
    language: selectedVoice?.language ?? "All",
    provider: "All",
    search: "",
  })
  const languages = useMemo(
    () =>
      [
        "All",
        ...new Set(
          catalog.voices
            .map((voice) => voice.language)
            .filter((language) => language !== "All"),
        ),
      ].sort((a, b) =>
        a === "All" ? -1 : b === "All" ? 1 : a.localeCompare(b),
      ),
    [catalog.voices],
  )
  const providers = useMemo(
    () => ["All", ...new Set(catalog.voices.map((voice) => voice.provider))],
    [catalog.voices],
  )
  // A plan that limits voices lists the ones it includes first.
  const visibleVoices = useMemo(() => {
    const voices = filterVoices(catalog.voices, filters)
    return [
      ...voices.filter((voice) => isVoiceAllowed(voice, allowedVoices)),
      ...voices.filter((voice) => !isVoiceAllowed(voice, allowedVoices)),
    ]
  }, [catalog.voices, filters, allowedVoices])
  // In columns (the Voice screen) the panels hang past the headings like every other
  // surface, so their content takes the same hang inset as the page's other cards.
  const inset = layout === "columns" ? "px-hang" : "px-4"
  const browseLabel = t("defaults.voice.browseVoices", {
    count: visibleVoices.length.toLocaleString(i18n.language),
  })
  const filterControls = (
    <div className={`grid gap-2 ${layout === "stacked" ? "grid-cols-3" : ""}`}>
      <VoiceFilter
        className={inset}
        label={t("defaults.voice.filters.language")}
        options={languages}
        renderOption={(language) =>
          language === "All" ? t("defaults.voice.filters.all") : language
        }
        value={filters.language}
        onChange={(language) =>
          setFilters((current) => ({ ...current, language }))
        }
      />
      <VoiceFilter
        className={inset}
        label={t("defaults.voice.filters.gender")}
        options={VOICE_GENDER_OPTIONS}
        renderOption={(gender) => {
          if (gender === "All") return t("defaults.voice.filters.all")
          if (gender === "Female") return t("defaults.voice.filters.female")
          return t("defaults.voice.filters.male")
        }}
        value={filters.gender}
        onChange={(gender) => setFilters((current) => ({ ...current, gender }))}
      />
      <VoiceFilter
        className={inset}
        label={t("defaults.voice.filters.provider")}
        options={providers}
        renderOption={(provider) =>
          provider === "All"
            ? t("defaults.voice.filters.all")
            : providerLabel(provider)
        }
        value={filters.provider}
        onChange={(provider) =>
          setFilters((current) => ({ ...current, provider }))
        }
      />
    </div>
  )
  const voiceRows =
    visibleVoices.length === 0 ? (
      <p className="py-12 text-center text-[13px] text-ink-muted">
        {t("defaults.voice.noVoices")}
      </p>
    ) : (
      <OptionList
        label={browseLabel}
        onValueChange={(key) => {
          const voice = visibleVoices.find((item) => voiceKey(item) === key)
          // Arrow keys choose the row they land on, so a locked voice does nothing
          // here; its own click and key handlers open the upgrade sheet.
          if (voice === undefined || !isVoiceAllowed(voice, allowedVoices))
            return
          onSelect({
            provider: voice.provider,
            model: voice.model,
            voiceId: voice.voiceId,
          })
        }}
        value={selectedVoice === undefined ? "" : voiceKey(selectedVoice)}
      >
        {visibleVoices.map((voice) => {
          const locked = !isVoiceAllowed(voice, allowedVoices)
          return (
            <OptionRow
              className={`py-2.5 ${inset}`}
              highlightSelected
              key={voiceKey(voice)}
              label={
                <span className={locked ? "opacity-40" : ""}>
                  {voice.name}
                  {locked && (
                    <span className="sr-only">
                      {" "}
                      {t("upgradeSheet.features.voice.cta")}
                    </span>
                  )}
                </span>
              }
              onClick={(event) => {
                if (locked && event.detail !== 0) openUpgradeSheet("voice")
              }}
              onKeyDown={(event) => {
                if (event.nativeEvent.isComposing) return
                if (locked && (event.key === "Enter" || event.key === " ")) {
                  openUpgradeSheet("voice")
                }
              }}
              trailing={
                <>
                  {allowedVoices !== null && !locked && (
                    <Pill tone="mint">{t("defaults.voice.free")}</Pill>
                  )}
                  <Pill className={locked ? "opacity-40" : ""}>
                    {providerLabel(voice.provider)}
                  </Pill>
                  {locked && <UpgradeLockIcon className="text-ink-muted" />}
                </>
              }
              value={voiceKey(voice)}
            />
          )
        })}
      </OptionList>
    )
  const searchAndList = (
    <>
      {/* In columns, the search text clears the 14px icon plus a 10px gap after the inset. */}
      <div className={`relative ${layout === "stacked" ? "mt-2" : ""}`}>
        <SearchIcon
          className={`pointer-events-none absolute top-1/2 -translate-y-1/2 text-ink-muted ${layout === "columns" ? "start-hang" : "start-3.5"}`}
          size={14}
        />
        <input
          aria-label={t("defaults.voice.searchVoices")}
          className={`h-9 w-full rounded-lg bg-white/[0.05] pe-3 text-sm ${layout === "columns" ? "ps-[calc(var(--spacing-hang)+24px)]" : "ps-9"} text-ink transition outline-none placeholder:text-ink-faint focus:bg-white/[0.07]`}
          onChange={(event) =>
            setFilters((current) => ({
              ...current,
              search: event.target.value,
            }))
          }
          placeholder={t("defaults.voice.searchPlaceholder")}
          value={filters.search}
        />
      </div>

      <div className="mt-2 flex min-h-0 flex-1 flex-col overflow-hidden rounded-xl bg-white/[0.05]">
        {listHeight === undefined && listMaxHeight === undefined ? (
          // The rows are absolutely positioned so they add nothing to the
          // page's height: the list takes whatever space the layout leaves it
          // and scrolls itself. As a normal flex child, a long catalog would
          // stretch every ancestor to its full height and scroll the page.
          <div className="relative min-h-48 flex-1">
            <div className="absolute inset-0 overflow-y-auto py-1.5">
              {voiceRows}
            </div>
          </div>
        ) : (
          <div
            className={`min-h-48 overflow-y-auto py-1.5 ${listHeight === undefined ? "flex-1" : "flex-none"}`}
            style={{ height: listHeight, maxHeight: listMaxHeight }}
          >
            {voiceRows}
          </div>
        )}
      </div>
    </>
  )

  return (
    <>
      {layout === "columns" ? (
        <div className="-mx-hang grid min-h-0 flex-1 grid-cols-[minmax(260px,0.8fr)_minmax(0,1.2fr)] items-stretch gap-6">
          <div className="flex min-h-0 flex-col">
            {children}
            <FieldLabel className="mt-5 px-hang">
              {t("defaults.voice.filterVoices")}
            </FieldLabel>
            {filterControls}
          </div>
          <div className="flex min-h-0 flex-col">
            <FieldLabel className="px-hang">{browseLabel}</FieldLabel>
            {searchAndList}
          </div>
        </div>
      ) : (
        <>
          {filterControls}
          {searchAndList}
        </>
      )}
    </>
  )
}

interface VoiceFilterProps {
  className: string
  label: string
  onChange: (value: string) => void
  options: string[]
  renderOption?: (value: string) => string
  value: string
}

const VoiceFilter = ({
  className,
  label,
  onChange,
  options,
  renderOption = (value) => value,
  value,
}: VoiceFilterProps) => (
  <Select onValueChange={onChange} value={value}>
    <SelectTrigger aria-label={label} className={className}>
      <span className="flex min-w-0 items-center gap-1 whitespace-nowrap">
        <span className="shrink-0 text-ink-muted">{label}:</span>
        <span className="truncate">
          <SelectValue />
        </span>
      </span>
    </SelectTrigger>
    <SelectContent>
      {options.map((option) => (
        <SelectItem key={option} value={option}>
          {renderOption(option)}
        </SelectItem>
      ))}
    </SelectContent>
  </Select>
)
