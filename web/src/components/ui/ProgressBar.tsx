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

interface ProgressBarProps {
  colorClass: string
  heightClass?: string
  percent: number
  trackClass?: string
}

export const ProgressBar = ({
  colorClass,
  heightClass = "h-1",
  percent,
  trackClass = "bg-white/[0.08]",
}: ProgressBarProps) => (
  <span
    className={`block overflow-hidden rounded-full ${heightClass} ${trackClass}`}
  >
    <span
      className={`block h-full rounded-full ${colorClass}`}
      style={{ width: `${Math.min(100, percent)}%` }}
    />
  </span>
)
