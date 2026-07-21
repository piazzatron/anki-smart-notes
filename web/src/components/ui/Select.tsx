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

import * as SelectPrimitive from "@radix-ui/react-select"
import { Check, ChevronDown } from "lucide-react"
import { forwardRef } from "react"

import type { ComponentPropsWithoutRef, ElementRef } from "react"

export const Select = SelectPrimitive.Root
export const SelectGroup = SelectPrimitive.Group
export const SelectValue = SelectPrimitive.Value

export const SelectTrigger = forwardRef<
  ElementRef<typeof SelectPrimitive.Trigger>,
  ComponentPropsWithoutRef<typeof SelectPrimitive.Trigger>
>(({ children, className = "", ...props }, ref) => (
  <SelectPrimitive.Trigger
    className={`flex min-h-11 w-full cursor-pointer items-center gap-2 rounded-md border border-white/[0.09] bg-white/[0.04] px-3 py-2 text-left text-xs font-medium text-zinc-100 transition outline-none hover:border-white/16 focus-visible:border-indigo/50 focus-visible:ring-2 focus-visible:ring-indigo/25 disabled:cursor-not-allowed disabled:opacity-45 data-[state=open]:border-indigo/50 data-[state=open]:ring-2 data-[state=open]:ring-indigo/25 ${className}`}
    ref={ref}
    {...props}
  >
    <span className="min-w-0 flex-1">{children}</span>
    <SelectPrimitive.Icon asChild>
      <ChevronDown aria-hidden className="size-4 shrink-0 text-ink-faint" />
    </SelectPrimitive.Icon>
  </SelectPrimitive.Trigger>
))
SelectTrigger.displayName = SelectPrimitive.Trigger.displayName

export const SelectContent = forwardRef<
  ElementRef<typeof SelectPrimitive.Content>,
  ComponentPropsWithoutRef<typeof SelectPrimitive.Content>
>(({ children, className = "", position = "popper", ...props }, ref) => (
  <SelectPrimitive.Portal>
    <SelectPrimitive.Content
      className={`z-50 max-h-[var(--radix-select-content-available-height)] min-w-[var(--radix-select-trigger-width)] overflow-hidden rounded-lg border border-white/10 bg-panel-raised text-zinc-100 shadow-[0_18px_40px_-12px_rgba(0,0,0,0.75)] ${className}`}
      position={position}
      ref={ref}
      sideOffset={6}
      {...props}
    >
      <SelectPrimitive.Viewport className="p-1">
        {children}
      </SelectPrimitive.Viewport>
    </SelectPrimitive.Content>
  </SelectPrimitive.Portal>
))
SelectContent.displayName = SelectPrimitive.Content.displayName

export const SelectLabel = forwardRef<
  ElementRef<typeof SelectPrimitive.Label>,
  ComponentPropsWithoutRef<typeof SelectPrimitive.Label>
>(({ className = "", ...props }, ref) => (
  <SelectPrimitive.Label
    className={`px-2.5 pt-2 pb-1 text-[10px] font-semibold tracking-[0.08em] text-ink-faint uppercase ${className}`}
    ref={ref}
    {...props}
  />
))
SelectLabel.displayName = SelectPrimitive.Label.displayName

export const SelectItem = forwardRef<
  ElementRef<typeof SelectPrimitive.Item>,
  ComponentPropsWithoutRef<typeof SelectPrimitive.Item>
>(({ children, className = "", ...props }, ref) => (
  <SelectPrimitive.Item
    className={`relative flex min-h-9 w-full cursor-pointer items-center rounded-md py-2 pr-2.5 pl-8 text-xs transition outline-none select-none data-[disabled]:pointer-events-none data-[disabled]:opacity-40 data-[highlighted]:bg-white/[0.06] data-[state=checked]:bg-indigo/14 ${className}`}
    ref={ref}
    {...props}
  >
    <span className="absolute left-2.5 flex size-3.5 items-center justify-center text-indigo-soft">
      <SelectPrimitive.ItemIndicator>
        <Check aria-hidden className="size-3.5" />
      </SelectPrimitive.ItemIndicator>
    </span>
    <SelectPrimitive.ItemText asChild>
      <span className="flex min-w-0 flex-1 items-center gap-3">{children}</span>
    </SelectPrimitive.ItemText>
  </SelectPrimitive.Item>
))
SelectItem.displayName = SelectPrimitive.Item.displayName
