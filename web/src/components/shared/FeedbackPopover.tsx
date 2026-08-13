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

import * as Popover from "@radix-ui/react-popover"
import { useEffect, useState, type ReactNode } from "react"

import { useFeedbackForm } from "./useFeedbackForm"

interface FeedbackPopoverProps {
  children: ReactNode
  onOpenSupport: () => void
}

export const FeedbackPopover = ({
  children,
  onOpenSupport,
}: FeedbackPopoverProps) => {
  const [open, setOpen] = useState(false)
  const form = useFeedbackForm()

  useEffect(() => {
    if (!form.state.sent) return
    const timeout = window.setTimeout(() => setOpen(false), 1500)
    return () => window.clearTimeout(timeout)
  }, [form.state.sent])

  return (
    <Popover.Root
      onOpenChange={(nextOpen) => {
        if (nextOpen) {
          form.patch({
            error: null,
            isSending: false,
            message: "",
            sent: false,
          })
        }
        setOpen(nextOpen)
      }}
      open={open}
    >
      <Popover.Trigger asChild>{children}</Popover.Trigger>
      <Popover.Portal>
        <Popover.Content
          align="start"
          className="z-40 w-[250px] rounded-[9px] border border-white/10 bg-panel-raised p-3 shadow-2xl shadow-black/40 outline-none"
          side="top"
          sideOffset={8}
        >
          {form.state.sent ? (
            <p className="text-xs text-mint">Sent — thanks!</p>
          ) : (
            <>
              <p className="text-xs font-medium text-zinc-100">Send feedback</p>
              <textarea
                aria-label="Feedback"
                className="mt-2 min-h-[64px] w-full resize-y rounded-md border border-white/10 bg-white/[0.03] px-2.5 py-2 text-xs text-zinc-200 outline-none placeholder:text-zinc-600 focus:border-indigo/45"
                onChange={(event) => form.setMessage(event.target.value)}
                placeholder="A bug, an idea, anything — it goes straight to the developer."
                value={form.state.message}
              />
              {form.state.error !== null && (
                <p className="mt-1.5 text-[10.5px] leading-4 text-danger">
                  {form.state.error}
                </p>
              )}
              <div className="mt-2.5 flex items-center justify-between gap-2">
                <button
                  className="text-left text-[11px] text-ink-muted hover:text-zinc-300"
                  onClick={() => {
                    setOpen(false)
                    onOpenSupport()
                  }}
                >
                  More support options
                </button>
                <button
                  className="rounded-md bg-mint px-3.5 py-1.5 text-[11.5px] font-medium text-emerald-950 disabled:opacity-45"
                  disabled={form.isSubmitDisabled}
                  onClick={() => void form.submit()}
                >
                  {form.state.isSending ? "Sending…" : "Send"}
                </button>
              </div>
            </>
          )}
        </Popover.Content>
      </Popover.Portal>
    </Popover.Root>
  )
}
