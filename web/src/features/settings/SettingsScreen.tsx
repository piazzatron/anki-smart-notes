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
import { useId, useState, type KeyboardEvent, type ReactNode } from "react"
import { Trans, useTranslation } from "react-i18next"

import { PageLayout } from "@/components/shared/PageLayout"
import { ScreenSkeleton } from "@/components/shared/ScreenSkeleton"
import { ErrorBanner } from "@/components/ui/ErrorBanner"
import { SectionHeading } from "@/components/ui/SectionHeading"
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
        <SectionHeading>{t("settings.sections.general")}</SectionHeading>
        <div className="-mx-[22px] flex items-center gap-5 rounded-xl bg-white/[0.05] px-[22px] py-[18px]">
          <div className="min-w-0 flex-1">
            <p className="text-sm font-medium text-ink">
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

      <div className="mt-10">
        <SectionHeading>{t("settings.sections.generation")}</SectionHeading>
        <div className="-mx-[22px] divide-y divide-white/[0.06] rounded-xl bg-white/[0.05] px-[22px]">
          <SettingRow
            checked={controls.values.generateOnAdd}
            description={t("settings.generateOnAdd.description")}
            disabled={controls.isSaving}
            label={t("settings.generateOnAdd.label")}
            onChange={(checked) =>
              void controls.update({ generateOnAdd: checked })
            }
          />
          <SettingRow
            checked={controls.values.generateAtReview}
            description={t("settings.generateAtReview.description")}
            disabled={controls.isSaving}
            label={t("settings.generateAtReview.label")}
            onChange={(checked) =>
              void controls.update({ generateAtReview: checked })
            }
          />
        </div>
      </div>

      <SectionHeading className="mt-10">
        {t("settings.sections.advanced")}
      </SectionHeading>
      <div className="-mx-[22px] divide-y divide-white/[0.06] rounded-xl bg-white/[0.05] px-[22px]">
        <SettingRow
          checked={controls.values.debug}
          description={t("settings.debug.description")}
          disabled={controls.isSaving}
          label={t("settings.debug.label")}
          onChange={(checked) => void controls.update({ debug: checked })}
        />
      </div>

      {settings.legacyOpenAiEnabled && (
        <div className="-mx-[22px] mt-3 divide-y divide-white/[0.06] rounded-xl bg-white/[0.05] px-[22px]">
          <button
            aria-expanded={legacyOpen}
            className="flex w-full cursor-pointer items-center gap-4 py-[18px] text-start"
            onClick={() => setLegacyOpen((open) => !open)}
            type="button"
          >
            <div className="min-w-0 flex-1">
              <p className="text-sm font-medium text-ink">
                {t("settings.legacy.title")}
              </p>
              <p className="mt-1 text-[13px] leading-5 text-ink-muted">
                {t("settings.legacy.description")}
              </p>
            </div>
            <ChevronRight
              aria-hidden
              className={`size-4 shrink-0 text-ink-faint transition-transform ${legacyOpen ? "rotate-90 rtl:-rotate-90" : "rtl:rotate-180"}`}
            />
          </button>

          {legacyOpen && (
            <div className="grid grid-cols-2 gap-4 py-5">
              <label className="block">
                <span className="text-[13px] font-semibold text-zinc-300">
                  {t("settings.legacy.apiKey")}
                </span>
                <input
                  className="mt-2 h-10 w-full rounded-lg bg-white/[0.05] px-3 text-[13px] text-zinc-200 outline-none focus:bg-white/[0.07]"
                  defaultValue={controls.values.legacyOpenAiKey ?? ""}
                  onBlur={(event) =>
                    void controls.update({
                      legacyOpenAiKey: event.currentTarget.value || null,
                    })
                  }
                  onKeyDown={saveOnEnter}
                  type="password"
                />
                <p className="mt-1.5 text-xs text-ink-muted">
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
                  className="block text-[13px] font-semibold text-zinc-300"
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
                <span className="text-[13px] font-semibold text-zinc-300">
                  {t("settings.legacy.host")}
                </span>
                <input
                  className="mt-2 h-10 w-full rounded-lg bg-white/[0.05] px-3 text-[13px] text-zinc-200 outline-none placeholder:text-zinc-600 focus:bg-white/[0.07]"
                  defaultValue={controls.values.legacyOpenAiHost ?? ""}
                  onBlur={(event) =>
                    void controls.update({
                      legacyOpenAiHost: event.currentTarget.value || null,
                    })
                  }
                  onKeyDown={saveOnEnter}
                  placeholder={t("settings.legacy.hostPlaceholder")}
                />
                <p className="mt-1.5 text-xs text-ink-muted">
                  {t("settings.legacy.hostDescription")}
                </p>
              </label>
            </div>
          )}
        </div>
      )}
      <SectionHeading className="mt-10" danger>
        {t("settings.sections.dangerZone")}
      </SectionHeading>
      <div className="-mx-[22px] divide-y divide-white/[0.06] rounded-xl bg-white/[0.05] px-[22px]">
        <SettingRow
          checked={controls.values.regenerateWhenBatching}
          description={t("settings.regenerateWhenBatching.description")}
          disabled={controls.isSaving}
          label={
            <Trans
              components={{ strong: <strong className="font-extrabold" /> }}
              i18nKey="settings.regenerateWhenBatching.label"
            />
          }
          onChange={(checked) =>
            void controls.update({ regenerateWhenBatching: checked })
          }
        />
      </div>
    </PageLayout>
  )
}

interface SettingRowProps {
  checked: boolean
  description: string
  disabled: boolean
  label: ReactNode
  onChange: (checked: boolean) => void
}

const SettingRow = ({
  checked,
  description,
  disabled,
  label,
  onChange,
}: SettingRowProps) => {
  // The label can carry markup (emphasis), so name the switch by the rendered
  // label rather than an aria-label string.
  const labelId = useId()
  return (
    <div className="flex items-center gap-5 py-[18px]">
      <div className="min-w-0 flex-1">
        <p className="text-sm font-medium text-ink" id={labelId}>
          {label}
        </p>
        <p className="mt-1 text-[13px] leading-5 text-ink-muted">
          {description}
        </p>
      </div>
      <Toggle
        aria-labelledby={labelId}
        checked={checked}
        disabled={disabled}
        onCheckedChange={onChange}
      />
    </div>
  )
}
