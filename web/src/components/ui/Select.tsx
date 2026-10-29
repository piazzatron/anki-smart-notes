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

import type { ComponentPropsWithoutRef, ElementRef, ReactNode } from "react"

export const Select = SelectPrimitive.Root
export const SelectGroup = SelectPrimitive.Group
export const SelectValue = SelectPrimitive.Value

export const SelectTrigger = forwardRef<
  ElementRef<typeof SelectPrimitive.Trigger>,
  ComponentPropsWithoutRef<typeof SelectPrimitive.Trigger>
>(({ children, className = "", ...props }, ref) => (
  <SelectPrimitive.Trigger
    className={`flex min-h-11 w-full cursor-pointer items-center gap-2 rounded-xl bg-white/[0.05] px-4 py-2 text-start text-sm font-medium text-ink transition outline-none hover:bg-white/[0.07] focus-visible:ring-2 focus-visible:ring-indigo/30 disabled:cursor-not-allowed disabled:opacity-45 data-[state=open]:bg-white/[0.08] ${className}`}
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
      className={`z-[80] max-h-[var(--radix-select-content-available-height)] min-w-[var(--radix-select-trigger-width)] origin-[var(--radix-select-content-transform-origin)] overflow-hidden rounded-xl bg-panel-raised text-ink shadow-[0_18px_40px_-12px_rgba(0,0,0,0.75)] duration-100 data-[side=bottom]:slide-in-from-top-2 data-[side=left]:slide-in-from-right-2 data-[side=right]:slide-in-from-left-2 data-[side=top]:slide-in-from-bottom-2 data-[state=closed]:animate-out data-[state=closed]:fade-out-0 data-[state=closed]:zoom-out-95 data-[state=open]:animate-in data-[state=open]:fade-in-0 data-[state=open]:zoom-in-95 ${className}`}
      position={position}
      ref={ref}
      sideOffset={6}
      {...props}
    >
      <SelectPrimitive.Viewport className="py-1.5">
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
    className={`px-4 pt-3 pb-1.5 text-[11px] font-semibold tracking-[0.055em] text-ink-muted uppercase ${className}`}
    ref={ref}
    {...props}
  />
))
SelectLabel.displayName = SelectPrimitive.Label.displayName

interface SelectItemProps extends ComponentPropsWithoutRef<
  typeof SelectPrimitive.Item
> {
  suffix?: ReactNode
}

// Rows run edge to edge with a hairline between neighbours (`.select-item` in
// globals.css), and a check marks the chosen one.
export const SelectItem = forwardRef<
  ElementRef<typeof SelectPrimitive.Item>,
  SelectItemProps
>(({ children, className = "", suffix, ...props }, ref) => (
  <SelectPrimitive.Item
    className={`select-item group relative flex min-h-10 w-full cursor-pointer items-center gap-2.5 px-4 py-2.5 text-sm font-medium text-ink transition outline-none select-none data-[disabled]:pointer-events-none data-[disabled]:opacity-40 data-[highlighted]:bg-white/[0.06] ${className}`}
    ref={ref}
    {...props}
  >
    <span className="flex size-3.5 shrink-0 items-center justify-center text-indigo-soft">
      <SelectPrimitive.ItemIndicator>
        <Check aria-hidden className="size-3.5" />
      </SelectPrimitive.ItemIndicator>
    </span>
    <SelectPrimitive.ItemText asChild>
      <span className="min-w-0 flex-1 truncate">{children}</span>
    </SelectPrimitive.ItemText>
    {suffix}
  </SelectPrimitive.Item>
))
SelectItem.displayName = SelectPrimitive.Item.displayName
