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

interface ScreenHeaderProps {
  accessory?: ReactNode
  icon: ReactNode
  subtitle: string
  title: string
}

export const ScreenHeader = ({
  accessory,
  icon,
  subtitle,
  title,
}: ScreenHeaderProps) => (
  <header className="flex shrink-0 items-center justify-between gap-6 border-b border-white/[0.065] px-6 py-5">
    <div className="min-w-0">
      <div className="flex items-center gap-2">
        {icon}
        <h1 className="truncate text-[21px] leading-tight font-bold tracking-[-0.025em] text-zinc-100">
          {title}
        </h1>
      </div>
      <p className="mt-1.5 truncate text-xs text-ink-muted">{subtitle}</p>
    </div>
    {accessory}
  </header>
)
