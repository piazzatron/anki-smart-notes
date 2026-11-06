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

import i18next from "i18next"
import type { ReactNode } from "react"

interface FieldLabelProps {
  as?: "p" | "span"
  children: ReactNode
  className?: string
  /** Marks the control as optional after the label. */
  optional?: boolean
}

/** The small label above a control or a panel: 12px, medium, muted, sentence case. */
export const FieldLabel = ({
  as: Component = "p",
  children,
  className = "",
  optional = false,
}: FieldLabelProps) => (
  <Component
    className={`mb-2 block text-xs font-medium text-ink-muted ${className}`}
  >
    {children}
    {optional && (
      <span className="ms-1 font-normal">{i18next.t("common.optional")}</span>
    )}
  </Component>
)
