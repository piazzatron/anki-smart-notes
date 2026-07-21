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

import { Check, ImageIcon } from "lucide-react"

interface StepDoneProps {
  targetFieldName: string
}

const GENERATION_METHODS = [
  {
    title: "In bulk, from the Browser",
    caption: "Select notes → right-click → Generate Smart Fields.",
  },
  {
    title: "One card at a time",
    caption:
      "Click the sparkle button in the editor toolbar — when adding or browsing (⌘⇧G).",
  },
  {
    title: "A single field",
    caption: "Right-click any field → Generate Smart Field.",
  },
]

export const StepDone = ({ targetFieldName }: StepDoneProps) => (
  <div>
    <div className="flex items-start gap-2.5">
      <span className="mt-0.5 inline-flex size-5 shrink-0 items-center justify-center rounded-full bg-mint/15 text-mint">
        <Check aria-hidden className="size-3.5" strokeWidth={2.5} />
      </span>
      <div>
        <h2 className="text-sm leading-5 text-zinc-100">
          <strong className="font-bold">{targetFieldName}</strong> is ready
        </h2>
        <p className="mt-0.5 text-[11.5px] leading-5 text-ink-muted">
          Smart Fields fill in when you generate them — three ways:
        </p>
      </div>
    </div>

    <div className="mt-4 space-y-2.5">
      {GENERATION_METHODS.map((method) => (
        <div
          className="grid grid-cols-[180px_1fr] items-center gap-4"
          key={method.title}
        >
          <div className="flex h-[100px] w-[180px] items-center justify-center rounded-lg border border-dashed border-white/[0.1] bg-white/[0.025] text-zinc-600">
            <span className="flex flex-col items-center gap-1.5 text-[10px] font-medium">
              <ImageIcon aria-hidden className="size-4" />
              screenshot
            </span>
          </div>
          <div className="min-w-0">
            <h3 className="text-[13px] font-semibold text-zinc-100">
              {method.title}
            </h3>
            <p className="mt-1 text-[11.5px] leading-[1.5] text-ink-muted">
              {method.caption}
            </p>
          </div>
        </div>
      ))}
    </div>
  </div>
)
