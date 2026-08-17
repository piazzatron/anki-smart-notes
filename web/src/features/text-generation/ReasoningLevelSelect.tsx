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

interface ReasoningLevelSelectProps {
  ariaLabel: string
  id?: string
  levels: string[]
  onValueChange: (level: string) => void
  value: string
}

/** How hard the model thinks, named by the catalog ("off", "low", "high"). */
export const ReasoningLevelSelect = ({
  ariaLabel,
  id,
  levels,
  onValueChange,
  value,
}: ReasoningLevelSelectProps) => (
  <Select onValueChange={onValueChange} value={value}>
    <SelectTrigger aria-label={ariaLabel} id={id}>
      <SelectValue />
    </SelectTrigger>
    <SelectContent>
      {levels.map((level) => (
        <SelectItem key={level} value={level}>
          <span className="font-semibold text-zinc-100 capitalize">
            {level}
          </span>
        </SelectItem>
      ))}
    </SelectContent>
  </Select>
)
