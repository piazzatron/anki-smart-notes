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

interface EditorSectionProps {
  children: ReactNode
  className?: string
  // A line under the heading, for a section whose purpose isn't self-evident.
  description?: string
  label: string
}

/** One headed block of the field editor. Both wizard steps use it, so they read at the
 * same scale — the small uppercase labels stay for settings nested inside a section. */
export const EditorSection = ({
  children,
  className = "",
  description,
  label,
}: EditorSectionProps) => (
  <section className={className}>
    <h2
      className={`text-[16px] leading-tight font-semibold text-zinc-100 ${description === undefined ? "mb-2" : "mb-1"}`}
    >
      {label}
    </h2>
    {description !== undefined && (
      <p className="mb-2 text-[12px] leading-[1.45] text-ink-muted">
        {description}
      </p>
    )}
    {children}
  </section>
)
