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

import { PageLayout } from "./PageLayout"

interface ScreenSkeletonProps {
  ariaLabel: string
  className?: string
  contentClassName: string
  showSubtitle?: boolean
  title: string
}

export const ScreenSkeleton = ({
  ariaLabel,
  className,
  contentClassName,
  showSubtitle = true,
  title,
}: ScreenSkeletonProps) => (
  <PageLayout
    className={className}
    subtitle={
      showSubtitle ? (
        <span className="block h-3 w-80 animate-pulse rounded bg-white/[0.035]" />
      ) : undefined
    }
    testId="screen-skeleton"
    title={title}
  >
    <div aria-label={ariaLabel} className="animate-pulse">
      <div className={`rounded-xl bg-white/[0.025] ${contentClassName}`} />
    </div>
  </PageLayout>
)
