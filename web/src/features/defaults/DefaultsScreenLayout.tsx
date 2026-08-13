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

import { LoaderCircle } from "lucide-react"
import type { ReactNode } from "react"

import { ScreenHeader } from "@/components/shared/ScreenHeader"

interface DefaultsScreenLayoutProps {
  accessory: ReactNode
  children: ReactNode
  icon: ReactNode
  subtitle: string
  tester: ReactNode
  testId: string
  title: string
}

export const DefaultsScreenLayout = ({
  accessory,
  children,
  icon,
  subtitle,
  tester,
  testId,
  title,
}: DefaultsScreenLayoutProps) => (
  <section className="flex min-h-0 flex-1 flex-col" data-testid={testId}>
    <ScreenHeader
      accessory={accessory}
      icon={icon}
      subtitle={subtitle}
      title={title}
    />
    {children}
    <div className="shrink-0 border-t border-white/[0.06] px-6 py-4">
      <div className="mx-auto w-full max-w-[640px]">{tester}</div>
    </div>
  </section>
)

export const DefaultsScreenLoading = ({ label }: { label: string }) => (
  <section className="flex min-h-0 flex-1 items-center justify-center">
    <LoaderCircle
      aria-label={label}
      className="size-5 animate-spin text-indigo-soft"
    />
  </section>
)
