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

import { InfoTip } from "@/components/ui/InfoTip"

interface SectionHeadingProps {
  children: ReactNode
  className?: string
  /** For a section of destructive settings, like Settings' danger zone. */
  danger?: boolean
  /** An optional ⓘ beside the heading: its accessible label and what it explains. */
  tip?: { label: string; content: ReactNode }
}

/** The heading above a group of settings, sized and spaced like Linear's settings
 *  sections. The surfaces below it hang past its left edge by their own padding. */
export const SectionHeading = ({
  children,
  className = "",
  danger = false,
  tip,
}: SectionHeadingProps) => (
  <h2
    className={`mb-[22px] flex items-center gap-1.5 text-base font-semibold ${danger ? "text-danger" : "text-ink"} ${className}`}
  >
    {children}
    {tip !== undefined && <InfoTip label={tip.label}>{tip.content}</InfoTip>}
  </h2>
)
