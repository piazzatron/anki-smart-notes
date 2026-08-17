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

import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/Select"
import { providerLabel } from "@/lib/catalog"
import type { TTSGenerationSettings, VoiceCatalog } from "@/types/api"

import { filterVoices, voiceKey, voiceMatchesSettings } from "./voiceDefaults"
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
  const selectedVoice = catalog.voices.find((voice) =>
    voiceMatchesSettings(voice, value),
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
  const visibleVoices = useMemo(
    () => filterVoices(catalog.voices, filters),
    [catalog.voices, filters],
  )
  const filterControls = (
    <div className={`grid gap-2 ${layout === "stacked" ? "grid-cols-3" : ""}`}>
      <VoiceFilter
        label="Language"
        options={languages}
        value={filters.language}
        onChange={(language) =>
          setFilters((current) => ({ ...current, language }))
        }
      />
      <VoiceFilter
        label="Gender"
        options={["All", "Female", "Male"]}
        value={filters.gender}
        onChange={(gender) => setFilters((current) => ({ ...current, gender }))}
      />
      <VoiceFilter
        label="Provider"
        options={providers}
        renderOption={(provider) =>
          provider === "All" ? "All" : providerLabel(provider)
        }
        value={filters.provider}
        onChange={(provider) =>
          setFilters((current) => ({ ...current, provider }))
        }
      />
    </div>
  )
  const searchAndList = (
    <>
      <input
        aria-label="Search voices"
        className={`${layout === "stacked" ? "mt-2" : ""} h-9 w-full rounded-lg border border-white/[0.09] bg-white/[0.035] px-3 text-xs text-zinc-200 transition outline-none placeholder:text-zinc-600 focus:border-indigo/45`}
        onChange={(event) =>
          setFilters((current) => ({
            ...current,
            search: event.target.value,
          }))
        }
        placeholder="🔍 Search voices…"
        value={filters.search}
      />

      <div className="mt-2 flex min-h-0 flex-1 flex-col overflow-hidden rounded-lg border border-white/[0.08] bg-black/10">
        <div
          className={`min-h-48 overflow-y-auto p-1.5 ${listHeight === undefined ? "flex-1" : "flex-none"}`}
          style={
            listHeight === undefined && listMaxHeight === undefined
              ? undefined
              : { height: listHeight, maxHeight: listMaxHeight }
          }
        >
          {visibleVoices.length === 0 ? (
            <p className="py-12 text-center text-xs text-ink-faint">
              No voices match these filters.
            </p>
          ) : (
            visibleVoices.map((voice) => {
              const key = voiceKey(voice)
              const isSelected = voiceMatchesSettings(voice, value)
              const selectVoice = () =>
                onSelect({
                  provider: voice.provider,
                  model: voice.model,
                  voiceId: voice.voiceId,
                })
              return (
                <div
                  className={`group flex cursor-pointer items-center gap-2 rounded-md px-2 py-2 transition ${isSelected ? "bg-indigo/14" : "hover:bg-white/[0.045]"}`}
                  key={key}
                  onClick={selectVoice}
                  role="button"
                  tabIndex={0}
                  onKeyDown={(event) => {
                    if (event.key === "Enter" || event.key === " ") {
                      event.preventDefault()
                      selectVoice()
                    }
                  }}
                >
                  <span className="min-w-0 flex-1 truncate text-xs font-semibold text-zinc-200">
                    {voice.name}
                  </span>
                  <span className="shrink-0 rounded bg-white/[0.045] px-2 py-0.5 text-[9.5px] text-ink-faint">
                    {providerLabel(voice.provider)}
                  </span>
                </div>
              )
            })
          )}
        </div>
      </div>
    </>
  )

  return (
    <>
      {layout === "columns" ? (
        <div className="grid min-h-0 flex-1 grid-cols-[minmax(260px,0.8fr)_minmax(0,1.2fr)] items-stretch gap-6">
          <div className="flex min-h-0 flex-col">
            {children}
            <p className="mt-5 mb-2 text-[10px] font-semibold tracking-[0.08em] text-ink-faint uppercase">
              Filter voices
            </p>
            {filterControls}
          </div>
          <div className="flex min-h-0 flex-col">
            <p className="mb-2 text-[10px] font-semibold tracking-[0.08em] text-ink-faint uppercase">
              Browse voices ({visibleVoices.length.toLocaleString()})
            </p>
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
  label: string
  onChange: (value: string) => void
  options: string[]
  renderOption?: (value: string) => string
  value: string
}

const VoiceFilter = ({
  label,
  onChange,
  options,
  renderOption = (value) => value,
  value,
}: VoiceFilterProps) => (
  <Select onValueChange={onChange} value={value}>
    <SelectTrigger aria-label={label} className="h-9 min-h-9 px-2.5 py-1.5">
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
