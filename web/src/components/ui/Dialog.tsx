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

import * as DialogPrimitive from "@radix-ui/react-dialog"
import { X } from "lucide-react"
import { forwardRef } from "react"

import type { ComponentPropsWithoutRef, ElementRef } from "react"

export const Dialog = DialogPrimitive.Root
export const DialogTrigger = DialogPrimitive.Trigger

// The modal shell: a dimmed backdrop, a centered card that scales in and out, and the
// dismiss affordance every dialog gets. Callers set the card's size and fill it.
export const DialogContent = forwardRef<
  ElementRef<typeof DialogPrimitive.Content>,
  ComponentPropsWithoutRef<typeof DialogPrimitive.Content>
>(({ children, className = "", ...props }, ref) => (
  <DialogPrimitive.Portal>
    <DialogPrimitive.Overlay className="fixed inset-0 z-[70] bg-black/70 data-[state=closed]:animate-overlay-out data-[state=open]:animate-overlay-in" />
    <DialogPrimitive.Content
      className={`fixed top-1/2 left-1/2 z-[70] flex -translate-x-1/2 -translate-y-1/2 flex-col overflow-hidden rounded-xl border border-white/[0.12] bg-[#16161b] shadow-2xl shadow-black/70 outline-none data-[state=closed]:animate-dialog-out data-[state=open]:animate-dialog-in ${className}`}
      ref={ref}
      {...props}
    >
      {children}
      <DialogPrimitive.Close
        aria-label="Close"
        className="absolute top-3.5 right-4 cursor-pointer text-zinc-500 transition hover:text-zinc-200"
      >
        <X aria-hidden className="size-4" />
      </DialogPrimitive.Close>
    </DialogPrimitive.Content>
  </DialogPrimitive.Portal>
))
DialogContent.displayName = DialogPrimitive.Content.displayName

// A dialog that takes the whole window rather than sitting in the middle of it: same
// layer, same escape and focus handling, but it brings its own backdrop and fills it.
export const DialogTakeover = forwardRef<
  ElementRef<typeof DialogPrimitive.Content>,
  ComponentPropsWithoutRef<typeof DialogPrimitive.Content>
>(({ children, className = "", ...props }, ref) => (
  <DialogPrimitive.Portal>
    <DialogPrimitive.Content
      className={`fixed inset-0 flex min-h-0 flex-col overflow-hidden outline-none data-[state=closed]:animate-zoom-out data-[state=open]:animate-zoom-in ${className}`}
      // Focus the takeover itself. It fills the window, so there is nothing to point
      // at, and the first control in it would otherwise open wearing a focus ring.
      onOpenAutoFocus={(event) => {
        event.preventDefault()
        if (event.currentTarget instanceof HTMLElement)
          event.currentTarget.focus()
      }}
      ref={ref}
      tabIndex={-1}
      {...props}
    >
      {children}
    </DialogPrimitive.Content>
  </DialogPrimitive.Portal>
))
DialogTakeover.displayName = "DialogTakeover"

// Title and description carry no type of their own: a takeover titles itself very
// differently from a small card, and there is no class merging to settle the argument.
export const DialogTitle = DialogPrimitive.Title
export const DialogDescription = DialogPrimitive.Description
