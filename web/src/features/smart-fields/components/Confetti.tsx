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

type ConfettiStyle = CSSProperties & {
  "--confetti-burst-x": string
  "--confetti-burst-y": string
  "--confetti-color": string
  "--confetti-delay": string
  "--confetti-duration": string
  "--confetti-end-x": string
  "--confetti-end-y": string
  "--confetti-mid-turn": string
  "--confetti-turn": string
}

const CONFETTI_PIECES = [
  [-320, -40, -390, 630, 210, 780, "var(--color-indigo)", 0.01, 2.35],
  [-290, 40, -355, 680, -190, -720, "var(--color-mint)", 0.04, 2.5],
  [-250, 110, -310, 700, 250, 840, "var(--color-pastel-butter)", 0.02, 2.4],
  [-220, -55, -270, 620, -220, -760, "var(--color-pastel-pink)", 0.07, 2.55],
  [-180, 155, -215, 720, 190, 700, "var(--color-pastel-sky)", 0, 2.3],
  [-140, 70, -165, 660, -240, -800, "var(--color-pastel-lavender)", 0.05, 2.45],
  [-95, -65, -115, 610, 220, 760, "var(--color-pastel-butter)", 0.03, 2.6],
  [-45, 180, -55, 730, -180, -680, "var(--color-mint)", 0.08, 2.25],
  [40, -70, 50, 600, 240, 820, "var(--color-pastel-pink)", 0.02, 2.55],
  [80, 170, 100, 720, -210, -740, "var(--color-indigo)", 0.06, 2.3],
  [130, 70, 160, 650, 190, 720, "var(--color-pastel-sky)", 0, 2.45],
  [175, -55, 215, 610, -230, -800, "var(--color-pastel-butter)", 0.04, 2.6],
  [220, 140, 270, 700, 220, 780, "var(--color-pastel-lavender)", 0.07, 2.35],
  [260, 45, 320, 660, -190, -720, "var(--color-mint)", 0.02, 2.5],
  [300, -35, 370, 620, 250, 840, "var(--color-pastel-pink)", 0.05, 2.4],
  [330, 100, 405, 690, -220, -760, "var(--color-indigo)", 0.01, 2.55],
] as const

/** A one-shot burst of confetti behind the first-field guide's title (its origin is set in `globals.css`). */
export const Confetti = () => (
  <div aria-hidden className="confetti">
    {CONFETTI_PIECES.map(
      ([burstX, burstY, endX, endY, midTurn, turn, color, delay, duration]) => (
        <i
          className="confetti-piece"
          key={`${burstX}-${burstY}`}
          style={
            {
              "--confetti-burst-x": `${burstX}px`,
              "--confetti-burst-y": `${burstY}px`,
              "--confetti-color": color,
              "--confetti-delay": `${delay}s`,
              "--confetti-duration": `${duration}s`,
              "--confetti-end-x": `${endX}px`,
              "--confetti-end-y": `${endY}px`,
              "--confetti-mid-turn": `${midTurn}deg`,
              "--confetti-turn": `${turn}deg`,
            } as ConfettiStyle
          }
        />
      ),
    )}
  </div>
)
