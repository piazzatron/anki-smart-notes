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

import * as RadioGroupPrimitive from "@radix-ui/react-radio-group"
import { Check } from "lucide-react"
import type { KeyboardEvent, MouseEvent, ReactNode } from "react"

interface OptionListProps {
  children: ReactNode
  className?: string
  /** The list's accessible name. */
  label: string
  /** Rows swallow Enter (in a radio group it doesn't choose), so a list that should
   *  react to it, like closing, listens here. */
  onKeyDown?: (event: KeyboardEvent<HTMLDivElement>) => void
  onValueChange: (value: string) => void
  /** The chosen row's value; one that matches no row leaves nothing chosen. */
  value: string
}

/** A list of choices that stays in the page, rather than popping up like `Select`: one
 *  tab stop, arrow keys to move and choose, in either text direction. Rows are
 *  `OptionRow`s, with group labels or anything else between them. */
export const OptionList = ({
  children,
  className = "",
  label,
  onKeyDown,
  onValueChange,
  value,
}: OptionListProps) => (
  <RadioGroupPrimitive.Root
    aria-label={label}
    className={className}
    onKeyDown={onKeyDown}
    onValueChange={onValueChange}
    orientation="vertical"
    value={value}
  >
    {children}
  </RadioGroupPrimitive.Root>
)

interface OptionRowProps {
  className?: string
  /** Also tint the chosen row and bold its label, for a list that stays on screen
   *  (the voice browser), so the choice reads at a glance. */
  highlightSelected?: boolean
  label: ReactNode
  /** Arrow keys choose by clicking the row for you, so a click with `event.detail` of 0
   *  came from the keyboard. */
  onClick?: (event: MouseEvent<HTMLButtonElement>) => void
  /** Shown at the row's end, like a cost or provider pill. */
  trailing?: ReactNode
  value: string
}

/** One row of an `OptionList`, in the app's dropdown row style: edge to edge, a hairline
 *  between rows, and a check in a fixed slot on the chosen one. Callers set the padding. */
export const OptionRow = ({
  className = "",
  highlightSelected = false,
  label,
  onClick,
  trailing,
  value,
}: OptionRowProps) => (
  <RadioGroupPrimitive.Item
    className={`group select-item relative flex w-full cursor-pointer items-center gap-2.5 text-start text-sm font-medium text-ink transition outline-none focus-visible:outline-2 focus-visible:-outline-offset-2 focus-visible:outline-indigo data-[state=unchecked]:hover:bg-white/[0.05] ${highlightSelected ? "data-[state=checked]:bg-indigo/[0.16]" : ""} ${className}`}
    onClick={onClick}
    value={value}
  >
    <span className="flex size-3.5 shrink-0 items-center justify-center text-indigo-soft">
      <RadioGroupPrimitive.Indicator>
        <Check aria-hidden className="size-3.5" />
      </RadioGroupPrimitive.Indicator>
    </span>
    <span
      className={`min-w-0 flex-1 truncate ${highlightSelected ? "group-data-[state=checked]:font-semibold" : ""}`}
    >
      {label}
    </span>
    {trailing}
  </RadioGroupPrimitive.Item>
)

/** The same keyboard and focus handling with no look of its own, for a choice drawn
 *  some other way (the Intelligence slider's stops). */
export const OptionGroup = RadioGroupPrimitive.Root
export const OptionGroupItem = RadioGroupPrimitive.Item
