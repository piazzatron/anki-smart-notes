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

import { Toggle } from "@/components/ui/Toggle"
import { ChatModelSelect } from "@/features/text-generation/ChatModelSelect"
import { ReasoningLevelSelect } from "@/features/text-generation/ReasoningLevelSelect"
import { TextModelGuidance } from "@/features/text-generation/TextModelGuidance"
import type { ChatGenerationSettings, ChatModelCatalog } from "@/types/api"
import { useTranslation } from "react-i18next"

interface TextModelSettingsProps {
  catalog: ChatModelCatalog
  onChange: (settings: ChatGenerationSettings) => void
  value: ChatGenerationSettings
}

export const TextModelSettings = ({
  catalog,
  onChange,
  value: settings,
}: TextModelSettingsProps) => {
  const { t } = useTranslation()
  return (
    <div className="space-y-4">
      <label className="block">
        <span className="mb-2 block text-[10px] font-semibold tracking-[0.06em] text-ink-faint uppercase">
          {t("fieldEditor.modelSettings.model")}
        </span>
        <ChatModelSelect
          ariaLabel={t("fieldEditor.modelSettings.textModel")}
          catalog={catalog}
          onValueChange={(model) =>
            onChange({ ...settings, model: model.id, provider: model.provider })
          }
          value={settings.model}
        />
        <TextModelGuidance />
      </label>

      {settings.provider === "auto" && (
        <label className="block">
          <span className="mb-2 block text-[10px] font-semibold tracking-[0.06em] text-ink-faint uppercase">
            {t("fieldEditor.modelSettings.reasoningLevel")}
          </span>
          <ReasoningLevelSelect
            ariaLabel={t("fieldEditor.modelSettings.reasoningLevel")}
            levels={catalog.reasoningLevels}
            onValueChange={(reasoningLevel) =>
              onChange({ ...settings, reasoningLevel })
            }
            value={settings.reasoningLevel}
          />
          <span className="mt-2 block text-[10.5px] leading-4 text-ink-muted">
            {t("fieldEditor.modelSettings.reasoningHint")}
          </span>
        </label>
      )}

      <div className="flex items-start justify-between gap-5 border-t border-white/[0.065] pt-4">
        <div>
          <p className="text-xs font-semibold text-zinc-200">
            {t("fieldEditor.modelSettings.webSearch")}
          </p>
          <p className="mt-1 text-[11px] leading-4 text-ink-muted">
            {t("fieldEditor.modelSettings.webSearchHint")}
          </p>
        </div>
        <Toggle
          aria-label={t("fieldEditor.modelSettings.useWebSearch")}
          checked={settings.webSearchEnabled}
          onCheckedChange={(webSearchEnabled) =>
            onChange({ ...settings, webSearchEnabled })
          }
        />
      </div>
    </div>
  )
}
