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

import type { CSSProperties } from "react"

export interface Sparkle {
  delay: string
  duration: string
  size: string
  left: string
  top: string
}

/** Slowly turning, twinkling sparkles behind a full-window moment (the welcome
 *  and free plan screens). Positions are percentages of the field. */
export const SparkleField = ({
  className,
  sparkles,
}: {
  className: string
  sparkles: readonly Sparkle[]
}) => (
  <div aria-hidden className={`pointer-events-none absolute ${className}`}>
    {sparkles.map((sparkle) => (
      <span
        className="welcome-sparkle"
        key={`${sparkle.left}-${sparkle.top}`}
        style={
          {
            "--welcome-sparkle-delay": sparkle.delay,
            "--welcome-sparkle-duration": sparkle.duration,
            fontSize: sparkle.size,
            left: sparkle.left,
            top: sparkle.top,
          } as CSSProperties
        }
      >
        {/* Decorative glyph; it has no language-specific meaning. */}
        {/* eslint-disable-next-line i18next/no-literal-string */}
        <span className="welcome-sparkle-glyph">✦</span>
      </span>
    ))}
  </div>
)
