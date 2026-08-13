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

interface CardProps {
  as?: "div" | "section"
  children: ReactNode
  className?: string
}

/** The quiet bordered surface shared by content cards across the app. */
export const Card = ({
  as: Component = "div",
  children,
  className = "",
}: CardProps) => (
  <Component
    className={`rounded-xl border border-white/[0.03] bg-white/[0.025] ${className}`}
  >
    {children}
  </Component>
)
