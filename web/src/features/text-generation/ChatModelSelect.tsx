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
} from "@/components/ui/Select"
import { modelCostLabel, modelLabel, providerLabel } from "@/lib/catalog"
import type { CatalogModel, ChatModelCatalog } from "@/types/api"

interface ChatModelSelectProps {
  ariaLabel?: string
  catalog: ChatModelCatalog
  id?: string
  onValueChange: (model: CatalogModel) => void
  value: string
}

// Only models. Whether a field follows its default is a separate choice, made outside
// this list — a shared setting doesn't belong in a list of models.
export const ChatModelSelect = ({
  ariaLabel,
  catalog,
  id,
  onValueChange,
  value,
}: ChatModelSelectProps) => (
  <Select
    onValueChange={(modelId) => onValueChange(getChatModel(catalog, modelId))}
    value={value}
  >
    <SelectTrigger aria-label={ariaLabel} id={id}>
      <ChatModelOption model={getChatModel(catalog, value)} />
    </SelectTrigger>
    <SelectContent>
      {catalog.providers.map((provider) => (
        <SelectGroup key={provider}>
          <SelectLabel>{providerLabel(provider)}</SelectLabel>
          {catalog.models
            .filter((model) => model.provider === provider)
            .map((model) => (
              <SelectItem key={model.id} value={model.id}>
                <ChatModelOption model={model} />
              </SelectItem>
            ))}
        </SelectGroup>
      ))}
    </SelectContent>
  </Select>
)

const ChatModelOption = ({ model }: { model: CatalogModel }) => {
  const costLabel = modelCostLabel(model.id)
  const isAutoModel = model.id === "auto" || model.id === "auto-max"

  return (
    <span className="flex min-w-0 items-center gap-2">
      <span
        className={`min-w-0 flex-1 truncate font-semibold ${isAutoModel ? "text-indigo-soft" : "text-zinc-100"}`}
      >
        {modelLabel(model.id)}
      </span>
      {costLabel !== undefined && (
        <span className="shrink-0 rounded bg-white/[0.06] px-2 py-0.5 text-[10px] font-semibold whitespace-nowrap text-zinc-400">
          {costLabel}
        </span>
      )}
    </span>
  )
}

const getChatModel = (
  catalog: ChatModelCatalog,
  modelId: string,
): CatalogModel => {
  const model = catalog.models.find((item) => item.id === modelId)
  if (model === undefined) {
    throw new Error(`Chat catalog is missing model ${modelId}`)
  }

  return model
}
