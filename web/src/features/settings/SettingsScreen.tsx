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

import { AlertCircle, ChevronRight, SlidersHorizontal, X } from "lucide-react"
import { useState, type KeyboardEvent } from "react"

import { Toggle } from "@/components/ui/Toggle"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/Select"
import { useAppStore } from "@/store/appStore"
import type { Settings } from "@/types/api"

import { useSettings } from "./useSettings"

const LEGACY_OPENAI_MODELS = [
  "gpt-5-chat-latest",
  "gpt-5",
  "gpt-5-mini",
  "gpt-4o",
  "gpt-4-turbo",
  "gpt-4",
  "o3-mini",
  "o1-mini",
  "gpt-4.1",
  "gpt-4.1-mini",
  "gpt-4.1-nano",
  "o3",
  "o4-mini",
]

export const SettingsScreen = () => {
  const state = useAppStore((store) => store.state)
  if (state === null) return <SettingsSkeleton />
  return <LoadedSettingsScreen settings={state.settings} />
}

interface LoadedSettingsScreenProps {
  settings: Settings
}

const LoadedSettingsScreen = ({ settings }: LoadedSettingsScreenProps) => {
  const controls = useSettings(settings)
  const [legacyOpen, setLegacyOpen] = useState(false)
  const saveOnEnter = (event: KeyboardEvent<HTMLInputElement>) => {
    if (event.key !== "Enter") return
    event.currentTarget.blur()
  }

  return (
    <section
      className="flex min-h-0 flex-1 flex-col"
      data-testid="settings-screen"
    >
      <header className="shrink-0 border-b border-white/[0.065] px-6 py-5">
        <div className="flex items-center gap-2">
          <SlidersHorizontal aria-hidden className="size-5 text-indigo-soft" />
          <h1 className="text-[21px] leading-tight font-bold tracking-[-0.025em] text-zinc-100">
            Settings
          </h1>
        </div>
        <p className="mt-1.5 text-xs text-ink-muted">
          How and when Smart Notes generates — plus the rarely-needed stuff.
        </p>
      </header>

      {controls.error !== null && (
        <div className="mx-6 mt-3 flex items-start gap-2 rounded-lg border border-red-300/15 bg-red-300/[0.06] px-3 py-2 text-xs text-danger">
          <AlertCircle aria-hidden className="mt-0.5 size-3.5 shrink-0" />
          <p className="min-w-0 flex-1">{controls.error}</p>
          <button aria-label="Dismiss error" onClick={controls.dismissError}>
            <X aria-hidden className="size-3.5" />
          </button>
        </div>
      )}

      <div className="min-h-0 flex-1 overflow-y-auto px-6 py-4">
        <div className="max-w-[680px]">
          <SectionLabel>Generation</SectionLabel>
          <div className="overflow-hidden rounded-xl border border-white/[0.08] bg-white/[0.02]">
            <SettingRow
              checked={controls.values.generateAtReview}
              description="Fill in missing smart fields automatically as cards come up in review."
              disabled={controls.isSaving}
              label="Generate fields during review"
              onChange={(checked) =>
                void controls.update({ generateAtReview: checked })
              }
            />
            <SettingRow
              checked={controls.values.regenerateWhenBatching}
              description="When batch processing a group of notes, regenerate every smart field from scratch instead of only filling empty ones."
              disabled={controls.isSaving}
              label="Regenerate all smart fields when batch processing"
              last
              onChange={(checked) =>
                void controls.update({ regenerateWhenBatching: checked })
              }
            />
          </div>

          <SectionLabel className="mt-5">Advanced</SectionLabel>
          <div className="overflow-hidden rounded-xl border border-white/[0.08] bg-white/[0.02]">
            <SettingRow
              checked={controls.values.debug}
              description="Verbose logging to help diagnose issues. Include these logs when filing a bug."
              disabled={controls.isSaving}
              label="Debug mode"
              last
              onChange={(checked) => void controls.update({ debug: checked })}
            />
          </div>

          <button
            aria-expanded={legacyOpen}
            className="mt-4 inline-flex items-center gap-1.5 text-[11px] text-ink-faint hover:text-zinc-400"
            onClick={() => setLegacyOpen((open) => !open)}
          >
            <ChevronRight
              aria-hidden
              className={`size-3 transition ${legacyOpen ? "rotate-90" : ""}`}
            />
            Use my own OpenAI key
          </button>

          {legacyOpen && (
            <div className="mt-2.5 rounded-xl border border-white/[0.08] bg-white/[0.02] p-4">
              <label className="block">
                <span className="text-[10px] font-semibold tracking-[0.08em] text-ink-faint uppercase">
                  OpenAI API key
                </span>
                <input
                  className="mt-2 h-10 w-full rounded-md border border-white/[0.09] bg-white/[0.035] px-3 text-xs text-zinc-200 outline-none focus:border-indigo/45"
                  defaultValue={controls.values.legacyOpenAiKey ?? ""}
                  onBlur={(event) =>
                    void controls.update({
                      legacyOpenAiKey: event.currentTarget.value || null,
                    })
                  }
                  onKeyDown={saveOnEnter}
                  type="password"
                />
              </label>
              <p className="mt-1.5 text-[11px] text-ink-muted">
                A paid OpenAI API key is required.{" "}
                <a
                  className="text-indigo-soft hover:underline"
                  href="https://platform.openai.com/account/api-keys/"
                  rel="noreferrer"
                  target="_blank"
                >
                  Get an API key
                </a>
              </p>

              <label className="mt-3 block text-[10px] font-semibold tracking-[0.08em] text-ink-faint uppercase">
                OpenAI model
              </label>
              <Select
                onValueChange={(legacyOpenAiModel) =>
                  void controls.update({ legacyOpenAiModel })
                }
                value={controls.values.legacyOpenAiModel}
              >
                <SelectTrigger
                  className="mt-2 min-h-10"
                  id="legacy-openai-model"
                >
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {LEGACY_OPENAI_MODELS.map((model) => (
                    <SelectItem key={model} value={model}>
                      {model}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>

              <label className="mt-3 block">
                <span className="text-[10px] font-semibold tracking-[0.08em] text-ink-faint uppercase">
                  OpenAI host
                </span>
                <input
                  className="mt-2 h-10 w-full rounded-md border border-white/[0.09] bg-white/[0.035] px-3 text-xs text-zinc-200 outline-none placeholder:text-zinc-600 focus:border-indigo/45"
                  defaultValue={controls.values.legacyOpenAiHost ?? ""}
                  onBlur={(event) =>
                    void controls.update({
                      legacyOpenAiHost: event.currentTarget.value || null,
                    })
                  }
                  onKeyDown={saveOnEnter}
                  placeholder="https://api.openai.com"
                />
              </label>
              <p className="mt-1.5 text-[11px] text-ink-muted">
                Provide an alternative endpoint to the OpenAI API.
              </p>
            </div>
          )}
        </div>
      </div>
    </section>
  )
}

interface SettingRowProps {
  checked: boolean
  description: string
  disabled: boolean
  label: string
  last?: boolean
  onChange: (checked: boolean) => void
}

const SettingRow = ({
  checked,
  description,
  disabled,
  label,
  last = false,
  onChange,
}: SettingRowProps) => (
  <div
    className={`flex items-center gap-3.5 px-4 py-3.5 ${
      last ? "" : "border-b border-white/[0.05]"
    }`}
  >
    <div className="min-w-0 flex-1">
      <p className="text-xs font-semibold text-zinc-200">{label}</p>
      <p className="mt-1 text-[11px] leading-[1.45] text-ink-muted">
        {description}
      </p>
    </div>
    <Toggle
      aria-label={label}
      checked={checked}
      disabled={disabled}
      onCheckedChange={onChange}
    />
  </div>
)

const SectionLabel = ({
  children,
  className = "",
}: {
  children: string
  className?: string
}) => (
  <h2
    className={`mb-2 text-[10px] font-semibold tracking-[0.08em] text-ink-faint uppercase ${className}`}
  >
    {children}
  </h2>
)

const SettingsSkeleton = () => (
  <section
    aria-label="Loading Settings"
    className="flex min-h-0 flex-1 animate-pulse flex-col"
  >
    <div className="h-[86px] border-b border-white/[0.065] px-6 py-5">
      <div className="h-5 w-36 rounded bg-white/[0.06]" />
      <div className="mt-3 h-3 w-80 rounded bg-white/[0.035]" />
    </div>
    <div className="p-6">
      <div className="h-36 max-w-[680px] rounded-xl bg-white/[0.025]" />
    </div>
  </section>
)
