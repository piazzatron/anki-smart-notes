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

import { LoaderCircle, Play } from "lucide-react"
import { useMemo, useState } from "react"

import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/Select"
import { ErrorBanner } from "@/components/ui/ErrorBanner"
import { providerLabel } from "@/lib/catalog"
import type { TTSGenerationSettings, VoiceCatalog } from "@/types/api"

import { filterVoices, voiceKey, voiceMatchesSettings } from "./voiceDefaults"
import { useVoicePreview } from "./useVoicePreview"

interface VoicePickerProps {
  canPreview: boolean
  catalog: VoiceCatalog
  listMaxHeight?: number
  onSelect: (settings: TTSGenerationSettings) => void
  value: TTSGenerationSettings
}

export const VoicePicker = ({
  canPreview,
  catalog,
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
  const voicePreview = useVoicePreview()
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

  return (
    <>
      {voicePreview.error !== null && (
        <ErrorBanner
          className="mb-3"
          message={voicePreview.error}
          onDismiss={voicePreview.dismissError}
        />
      )}

      <div className="grid grid-cols-3 gap-2">
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
          onChange={(gender) =>
            setFilters((current) => ({ ...current, gender }))
          }
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

      <input
        aria-label="Search voices"
        className="mt-2 h-9 w-full rounded-md border border-white/[0.09] bg-white/[0.035] px-3 text-xs text-zinc-200 transition outline-none placeholder:text-zinc-600 focus:border-indigo/45"
        onChange={(event) =>
          setFilters((current) => ({
            ...current,
            search: event.target.value,
          }))
        }
        placeholder={`🔍 Search ${catalog.voices.length} voices…`}
        value={filters.search}
      />

      <div className="mt-2 flex min-h-0 flex-1 flex-col overflow-hidden rounded-lg border border-white/[0.08] bg-black/10">
        <div
          className="min-h-48 flex-1 overflow-y-auto p-1.5"
          style={
            listMaxHeight === undefined
              ? undefined
              : { maxHeight: listMaxHeight }
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
                  <button
                    aria-label={`Preview ${voice.name}`}
                    className="flex size-4 shrink-0 cursor-pointer items-center justify-center text-zinc-500 transition hover:text-indigo-soft disabled:cursor-not-allowed disabled:opacity-35"
                    disabled={!canPreview || voicePreview.loadingKey !== null}
                    onClick={(event) => {
                      event.stopPropagation()
                      void voicePreview.preview(voice)
                    }}
                  >
                    {voicePreview.loadingKey === key ? (
                      <LoaderCircle
                        aria-hidden
                        className="size-3 animate-spin"
                      />
                    ) : (
                      <Play
                        aria-hidden
                        className="ml-0.5 size-2.5 fill-current"
                      />
                    )}
                  </button>
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
