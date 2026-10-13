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
import * as TooltipPrimitive from "@radix-ui/react-tooltip"
import { Info } from "lucide-react"
import type { ReactNode } from "react"

interface InfoTipProps {
  children: ReactNode
  label: string
}

/** An ⓘ beside a setting that explains it on hover or focus. Tooltips are always a
 *  flat blue fill with no border. */
export const InfoTip = ({ children, label }: InfoTipProps) => (
  <TooltipPrimitive.Provider delayDuration={150}>
    <TooltipPrimitive.Root>
      <TooltipPrimitive.Trigger asChild>
        <button
          aria-label={label}
          className="inline-flex size-4 shrink-0 items-center justify-center rounded-full text-ink-faint transition hover:text-indigo-soft"
          type="button"
        >
          <Info aria-hidden className="size-3.5" />
        </button>
      </TooltipPrimitive.Trigger>
      <TooltipPrimitive.Portal>
        <TooltipPrimitive.Content
          className="z-[90] max-w-[300px] rounded-lg bg-indigo-deep px-3 py-2 text-[11.5px] leading-[1.5] font-normal tracking-normal text-white normal-case shadow-xl shadow-black/40"
          collisionPadding={12}
          side="right"
          sideOffset={6}
        >
          {children}
          {/* A wide, round-tipped caret instead of Radix's sharp triangle, to match the
              app's soft corners. */}
          <TooltipPrimitive.Arrow asChild height={5.5} width={18}>
            <svg className="fill-indigo-deep" viewBox="0 0 18 5.5">
              <path d="M0 0L6.16 4.45Q9 6.5 11.84 4.45L18 0Z" />
            </svg>
          </TooltipPrimitive.Arrow>
        </TooltipPrimitive.Content>
      </TooltipPrimitive.Portal>
    </TooltipPrimitive.Root>
  </TooltipPrimitive.Provider>
)
