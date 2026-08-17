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
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/Select"
import { modelLabel } from "@/lib/catalog"
import type { ImageGenerationSettings, ImageModelCatalog } from "@/types/api"

interface ImageModelSelectProps {
  ariaLabel?: string
  catalog: ImageModelCatalog
  id?: string
  onValueChange: (settings: ImageGenerationSettings) => void
  value: string
}

export const ImageModelSelect = ({
  ariaLabel,
  catalog,
  id,
  onValueChange,
  value,
}: ImageModelSelectProps) => (
  <Select
    onValueChange={(model) => {
      const selected = catalog.models.find((item) => item.id === model)
      if (selected === undefined) {
        throw new Error(`Image catalog is missing model ${model}`)
      }
      onValueChange({ model, provider: selected.provider })
    }}
    value={value}
  >
    <SelectTrigger aria-label={ariaLabel} id={id}>
      <SelectValue />
    </SelectTrigger>
    <SelectContent>
      {catalog.models.map((model) => (
        <SelectItem key={`${model.provider}:${model.id}`} value={model.id}>
          <span className="min-w-0 flex-1 truncate font-semibold text-zinc-100">
            {modelLabel(model.id)}
          </span>
        </SelectItem>
      ))}
    </SelectContent>
  </Select>
)
