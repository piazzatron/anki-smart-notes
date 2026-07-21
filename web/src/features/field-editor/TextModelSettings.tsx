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
  SelectGroup,
  SelectItem,
  SelectLabel,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/Select"
import { Toggle } from "@/components/ui/Toggle"
import { modelCostLabel, modelLabel, providerLabel } from "@/lib/catalog"
import type { Catalog, ChatGenerationSettings } from "@/types/api"

interface TextModelSettingsProps {
  catalog: Catalog
  onChange: (settings: ChatGenerationSettings) => void
  value: ChatGenerationSettings
}

export const TextModelSettings = ({
  catalog,
  onChange,
  value,
}: TextModelSettingsProps) => (
  <div className="space-y-4">
    <label className="block">
      <span className="mb-2 block text-[10px] font-semibold tracking-[0.06em] text-ink-faint uppercase">
        Model
      </span>
      <Select
        onValueChange={(model) => {
          const selected = catalog.chat.models.find((item) => item.id === model)
          if (selected === undefined)
            throw new Error(`Chat catalog is missing model ${model}`)
          onChange({ ...value, model, provider: selected.provider })
        }}
        value={value.model}
      >
        <SelectTrigger aria-label="Text model">
          <SelectValue />
        </SelectTrigger>
        <SelectContent>
          {catalog.chat.providers.map((provider) => (
            <SelectGroup key={provider}>
              <SelectLabel>{providerLabel(provider)}</SelectLabel>
              {catalog.chat.models
                .filter((model) => model.provider === provider)
                .map((model) => (
                  <SelectItem key={model.id} value={model.id}>
                    <span className="min-w-0 flex-1 truncate font-semibold text-zinc-100">
                      {modelLabel(model.id)}
                    </span>
                    {modelCostLabel(model.id) !== undefined && (
                      <span className="shrink-0 rounded bg-white/[0.06] px-2 py-0.5 text-[10px] font-semibold text-zinc-400">
                        {modelCostLabel(model.id)}
                      </span>
                    )}
                  </SelectItem>
                ))}
            </SelectGroup>
          ))}
        </SelectContent>
      </Select>
    </label>

    {value.provider === "auto" && (
      <label className="block">
        <span className="mb-2 block text-[10px] font-semibold tracking-[0.06em] text-ink-faint uppercase">
          Reasoning level
        </span>
        <Select
          onValueChange={(reasoningLevel) =>
            onChange({ ...value, reasoningLevel })
          }
          value={value.reasoningLevel}
        >
          <SelectTrigger aria-label="Reasoning level">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            {catalog.chat.reasoningLevels.map((level) => (
              <SelectItem key={level} value={level}>
                {level === "off"
                  ? "Off"
                  : `${level.charAt(0).toUpperCase()}${level.slice(1)}`}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </label>
    )}

    <div className="flex items-start justify-between gap-5 border-t border-white/[0.065] pt-4">
      <div>
        <p className="text-xs font-semibold text-zinc-200">Web search</p>
        <p className="mt-1 text-[11px] leading-4 text-ink-muted">
          Let this field use fresh information from the web.
        </p>
      </div>
      <Toggle
        aria-label="Use web search for this field"
        checked={value.webSearchEnabled}
        onCheckedChange={(webSearchEnabled) =>
          onChange({ ...value, webSearchEnabled })
        }
      />
    </div>
  </div>
)
