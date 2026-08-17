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

import { PageTitle } from "./PageTitle"

interface PageLayoutProps {
  actions?: ReactNode
  children: ReactNode
  className?: string
  icon?: ReactNode
  subtitle?: ReactNode
  testId: string
  title: string
}

/** The shared title, inset, width, and scrolling shell for top-level app pages. */
export const PageLayout = ({
  actions,
  children,
  className = "",
  icon,
  subtitle,
  testId,
  title,
}: PageLayoutProps) => (
  <section className="flex min-h-0 flex-1 flex-col" data-testid={testId}>
    <div className="min-h-0 flex-1 overflow-y-auto px-8 py-7">
      <div className={`flex min-h-full w-full flex-col ${className}`}>
        <header className="flex shrink-0 items-start justify-between gap-6 border-b border-white/[0.07] pb-5">
          <div className="min-w-0">
            <div className="flex items-center gap-2">
              {icon}
              <PageTitle>{title}</PageTitle>
            </div>
            {subtitle !== undefined && (
              <div className="mt-1.5 truncate text-xs text-ink-muted">
                {subtitle}
              </div>
            )}
          </div>
          {actions}
        </header>
        <div className="mt-6 flex min-h-0 flex-1 flex-col">{children}</div>
      </div>
    </div>
  </section>
)
