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

import { ChevronRight } from "lucide-react"
import { useState, type KeyboardEvent } from "react"

import { PageLayout } from "@/components/shared/PageLayout"
import { ScreenSkeleton } from "@/components/shared/ScreenSkeleton"
import { ErrorBanner } from "@/components/ui/ErrorBanner"
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
  if (state === null)
    return (
      <ScreenSkeleton
        ariaLabel="Loading Settings"
        className="max-w-[800px]"
        contentClassName="h-36 max-w-[680px]"
        title="Settings"
      />
    )
  return <LoadedSettingsScreen settings={state.settings} />
}

interface LoadedSettingsScreenProps {
  settings: Settings
}

export const LoadedSettingsScreen = ({
  settings,
}: LoadedSettingsScreenProps) => {
  const controls = useSettings(settings)
  const [legacyOpen, setLegacyOpen] = useState(false)
  const saveOnEnter = (event: KeyboardEvent<HTMLInputElement>) => {
    if (event.key !== "Enter") return
    event.currentTarget.blur()
  }

  return (
    <PageLayout
      className="max-w-[800px]"
      testId="settings-screen"
      title="Settings"
    >
      {controls.error !== null && (
        <ErrorBanner
          className="mb-5"
          message={controls.error}
          onDismiss={controls.dismissError}
        />
      )}

      <div>
        <SectionLabel>Generation</SectionLabel>
        <div>
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
            onChange={(checked) =>
              void controls.update({ regenerateWhenBatching: checked })
            }
          />
        </div>
      </div>

      <SectionLabel className="mt-8">Advanced</SectionLabel>
      <div>
        <SettingRow
          checked={controls.values.debug}
          description="Verbose logging to help diagnose issues. Include these logs when filing a bug."
          disabled={controls.isSaving}
          label="Debug mode"
          onChange={(checked) => void controls.update({ debug: checked })}
        />
      </div>

      {settings.legacyOpenAiEnabled && (
        <>
          <button
            aria-expanded={legacyOpen}
            className="flex w-full items-center gap-4 border-b border-white/[0.065] py-4 text-left"
            onClick={() => setLegacyOpen((open) => !open)}
            type="button"
          >
            <div className="min-w-0 flex-1">
              <p className="text-[15px] font-semibold text-zinc-100">
                Use my own OpenAI key
              </p>
              <p className="mt-1 text-[13px] leading-5 text-ink-muted">
                Connect a paid API key and choose a legacy OpenAI model.
              </p>
            </div>
            <ChevronRight
              aria-hidden
              className={`size-5 shrink-0 text-zinc-500 transition-transform ${legacyOpen ? "rotate-90" : ""}`}
            />
          </button>

          {legacyOpen && (
            <div className="grid grid-cols-2 gap-4 border-b border-white/[0.065] py-5">
              <label className="block">
                <span className="text-xs font-semibold text-zinc-300">
                  OpenAI API key
                </span>
                <input
                  className="mt-2 h-10 w-full rounded-lg border border-white/[0.09] bg-white/[0.035] px-3 text-xs text-zinc-200 outline-none focus:border-indigo/45"
                  defaultValue={controls.values.legacyOpenAiKey ?? ""}
                  onBlur={(event) =>
                    void controls.update({
                      legacyOpenAiKey: event.currentTarget.value || null,
                    })
                  }
                  onKeyDown={saveOnEnter}
                  type="password"
                />
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
              </label>

              <div>
                <label
                  className="block text-xs font-semibold text-zinc-300"
                  htmlFor="legacy-openai-model"
                >
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
              </div>

              <label className="col-span-2 block">
                <span className="text-xs font-semibold text-zinc-300">
                  OpenAI host
                </span>
                <input
                  className="mt-2 h-10 w-full rounded-lg border border-white/[0.09] bg-white/[0.035] px-3 text-xs text-zinc-200 outline-none placeholder:text-zinc-600 focus:border-indigo/45"
                  defaultValue={controls.values.legacyOpenAiHost ?? ""}
                  onBlur={(event) =>
                    void controls.update({
                      legacyOpenAiHost: event.currentTarget.value || null,
                    })
                  }
                  onKeyDown={saveOnEnter}
                  placeholder="https://api.openai.com"
                />
                <p className="mt-1.5 text-[11px] text-ink-muted">
                  Provide an alternative endpoint to the OpenAI API.
                </p>
              </label>
            </div>
          )}
        </>
      )}
    </PageLayout>
  )
}

interface SettingRowProps {
  checked: boolean
  description: string
  disabled: boolean
  label: string
  onChange: (checked: boolean) => void
}

const SettingRow = ({
  checked,
  description,
  disabled,
  label,
  onChange,
}: SettingRowProps) => (
  <div className="flex min-h-[76px] items-center gap-5 border-b border-white/[0.065] py-4">
    <div className="min-w-0 flex-1">
      <p className="text-[15px] font-semibold text-zinc-100">{label}</p>
      <p className="mt-1 text-[13px] leading-5 text-ink-muted">{description}</p>
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
  <h2 className={`mb-1 text-[15px] font-semibold text-zinc-400 ${className}`}>
    {children}
  </h2>
)
