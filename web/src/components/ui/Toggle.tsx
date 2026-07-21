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

interface ToggleProps {
  "aria-label": string
  checked: boolean
  disabled?: boolean
  onCheckedChange: (checked: boolean) => void
}

export const Toggle = ({
  "aria-label": ariaLabel,
  checked,
  disabled = false,
  onCheckedChange,
}: ToggleProps) => (
  <button
    aria-checked={checked}
    aria-label={ariaLabel}
    className={`relative h-5 w-9 shrink-0 rounded-full transition ${
      checked ? "bg-indigo" : "bg-white/10"
    }`}
    disabled={disabled}
    onClick={() => onCheckedChange(!checked)}
    role="switch"
    type="button"
  >
    <span
      className={`absolute top-0.5 size-4 rounded-full bg-white shadow transition ${
        checked ? "left-[18px]" : "left-0.5"
      }`}
    />
  </button>
)
