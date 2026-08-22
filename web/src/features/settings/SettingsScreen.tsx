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
import { useTranslation } from "react-i18next"

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
import { changeAppLanguage } from "@/lib/i18n"
import { LANGUAGES } from "@/lib/i18n/languages"
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
  const { t } = useTranslation()
  const state = useAppStore((store) => store.state)
  if (state === null)
    return (
      <ScreenSkeleton
        ariaLabel={t("settings.loading")}
        className="max-w-[800px]"
        contentClassName="h-36 max-w-[680px]"
        title={t("settings.title")}
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
  const { t } = useTranslation()
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
      title={t("settings.title")}
    >
      {controls.error !== null && (
        <ErrorBanner
          className="mb-5"
          message={controls.error}
          onDismiss={controls.dismissError}
        />
      )}

      <div>
        <SectionLabel>{t("settings.sections.general")}</SectionLabel>
        <div className="flex min-h-[76px] items-center gap-5 border-b border-white/[0.065] py-4">
          <div className="min-w-0 flex-1">
            <p className="text-[15px] font-semibold text-zinc-100">
              {t("settings.language.label")}
            </p>
            <p className="mt-1 text-[13px] leading-5 text-ink-muted">
              {t("settings.language.description")}
            </p>
          </div>
          <div className="w-48 shrink-0">
            <label className="sr-only" htmlFor="app-language">
              {t("settings.language.label")}
            </label>
            <Select
              disabled={controls.isSaving}
              onValueChange={(language) =>
                void controls.update({ language }, () =>
                  changeAppLanguage(language),
                )
              }
              value={controls.values.language}
            >
              <SelectTrigger id="app-language">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="auto">
                  {t("settings.language.matchAnki")}
                </SelectItem>
                {LANGUAGES.map((language) => (
                  <SelectItem
                    key={language.bcp47}
                    textValue={language.nativeName}
                    value={language.bcp47}
                  >
                    <span className="inline-flex items-center gap-2">
                      <span>{language.nativeName}</span>
                      <span aria-hidden className="w-5 text-center text-base">
                        {language.flag}
                      </span>
                    </span>
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        </div>
      </div>

      <div className="mt-8">
        <SectionLabel>{t("settings.sections.generation")}</SectionLabel>
        <div>
          <SettingRow
            checked={controls.values.generateAtReview}
            description={t("settings.generateAtReview.description")}
            disabled={controls.isSaving}
            label={t("settings.generateAtReview.label")}
            onChange={(checked) =>
              void controls.update({ generateAtReview: checked })
            }
          />
          <SettingRow
            checked={controls.values.regenerateWhenBatching}
            description={t("settings.regenerateWhenBatching.description")}
            disabled={controls.isSaving}
            label={t("settings.regenerateWhenBatching.label")}
            onChange={(checked) =>
              void controls.update({ regenerateWhenBatching: checked })
            }
          />
        </div>
      </div>

      <SectionLabel className="mt-8">
        {t("settings.sections.advanced")}
      </SectionLabel>
      <div>
        <SettingRow
          checked={controls.values.debug}
          description={t("settings.debug.description")}
          disabled={controls.isSaving}
          label={t("settings.debug.label")}
          onChange={(checked) => void controls.update({ debug: checked })}
        />
      </div>

      {settings.legacyOpenAiEnabled && (
        <>
          <button
            aria-expanded={legacyOpen}
            className="flex w-full items-center gap-4 border-b border-white/[0.065] py-4 text-start"
            onClick={() => setLegacyOpen((open) => !open)}
            type="button"
          >
            <div className="min-w-0 flex-1">
              <p className="text-[15px] font-semibold text-zinc-100">
                {t("settings.legacy.title")}
              </p>
              <p className="mt-1 text-[13px] leading-5 text-ink-muted">
                {t("settings.legacy.description")}
              </p>
            </div>
            <ChevronRight
              aria-hidden
              className={`size-5 shrink-0 text-zinc-500 transition-transform ${legacyOpen ? "rotate-90 rtl:-rotate-90" : "rtl:rotate-180"}`}
            />
          </button>

          {legacyOpen && (
            <div className="grid grid-cols-2 gap-4 border-b border-white/[0.065] py-5">
              <label className="block">
                <span className="text-xs font-semibold text-zinc-300">
                  {t("settings.legacy.apiKey")}
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
                  {t("settings.legacy.apiKeyRequired")}{" "}
                  <a
                    className="text-indigo-soft hover:underline"
                    href="https://platform.openai.com/account/api-keys/"
                    rel="noreferrer"
                    target="_blank"
                  >
                    {t("settings.legacy.getApiKey")}
                  </a>
                </p>
              </label>

              <div>
                <label
                  className="block text-xs font-semibold text-zinc-300"
                  htmlFor="legacy-openai-model"
                >
                  {t("settings.legacy.model")}
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
                  {t("settings.legacy.host")}
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
                  placeholder={t("settings.legacy.hostPlaceholder")}
                />
                <p className="mt-1.5 text-[11px] text-ink-muted">
                  {t("settings.legacy.hostDescription")}
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
