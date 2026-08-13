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
import { Button } from "@/components/ui/Button"
import { Card } from "@/components/ui/Card"

interface DefaultsScreenLayoutProps {
  accessory: ReactNode
  children: ReactNode
  contentFillsHeight?: boolean
  icon: ReactNode
  isDirty: boolean
  isSaving: boolean
  onSave: () => void
  subtitle: string
  tester: ReactNode
  testId: string
  title: string
}

export const DefaultsScreenLayout = ({
  accessory,
  children,
  contentFillsHeight = false,
  icon,
  isDirty,
  isSaving,
  onSave,
  subtitle,
  tester,
  testId,
  title,
}: DefaultsScreenLayoutProps) => (
  <section className="flex min-h-0 flex-1 flex-col" data-testid={testId}>
    <ScreenHeader
      accessory={
        <div className="flex items-center gap-3">
          {accessory}
          {isDirty && (
            <Button disabled={isSaving} onClick={onSave} variant="primary">
              {isSaving ? "Saving…" : "Save changes"}
            </Button>
          )}
        </div>
      }
      icon={icon}
      subtitle={subtitle}
      title={title}
    />
    <div
      className={`min-h-0 flex-1 overflow-y-auto ${contentFillsHeight ? "flex flex-col" : ""}`}
    >
      {children}
      <div className="px-6 pt-2 pb-6">
        <h2 className="mb-3 text-[17px] leading-tight font-bold text-zinc-100">
          Try it
        </h2>
        <Card className="w-full p-4">{tester}</Card>
      </div>
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
