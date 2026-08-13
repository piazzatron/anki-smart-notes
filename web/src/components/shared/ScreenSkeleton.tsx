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

interface ScreenSkeletonProps {
  ariaLabel: string
  contentClassName: string
  showSubtitle?: boolean
}

export const ScreenSkeleton = ({
  ariaLabel,
  contentClassName,
  showSubtitle = true,
}: ScreenSkeletonProps) => (
  <section
    aria-label={ariaLabel}
    className="flex min-h-0 flex-1 animate-pulse flex-col"
  >
    <div className="h-[86px] border-b border-white/[0.065] px-6 py-5">
      <div className="h-5 w-44 rounded bg-white/[0.06]" />
      {showSubtitle && (
        <div className="mt-3 h-3 w-80 rounded bg-white/[0.035]" />
      )}
    </div>
    <div className="p-6">
      <div className={`rounded-xl bg-white/[0.025] ${contentClassName}`} />
    </div>
  </section>
)
