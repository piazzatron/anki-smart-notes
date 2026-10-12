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

import type { ReactNode } from "react"

interface PillProps {
  children: ReactNode
  className?: string
  tone?: "neutral" | "indigo" | "amber" | "warning"
}

const TONE_CLASSES = {
  neutral: "bg-white/[0.08] text-zinc-300",
  indigo: "bg-indigo/22 text-indigo-soft",
  amber: "bg-amber/[0.14] text-amber",
  // Solid, for costs people must not miss.
  warning: "bg-amber text-zinc-950",
}

/** The small rounded label shared across the app for metadata: decks, costs,
 *  providers, usage, and what a test ran with. Fill only — pills never get a border. */
export const Pill = ({
  children,
  className = "",
  tone = "neutral",
}: PillProps) => (
  <span
    className={`inline-flex shrink-0 items-center rounded-full px-2.5 py-[3px] text-[10.5px] leading-4 font-semibold whitespace-nowrap ${TONE_CLASSES[tone]} ${className}`}
  >
    {children}
  </span>
)
