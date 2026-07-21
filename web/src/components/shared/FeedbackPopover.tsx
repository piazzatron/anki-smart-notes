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

import { useEffect, useRef, useState } from "react"

import { sendFeedback } from "@/services/commands"

interface FeedbackPopoverProps {
  onClose: () => void
  onOpenSupport: () => void
}

interface FeedbackState {
  message: string
  error: string | null
  isSending: boolean
  sent: boolean
}

export const FeedbackPopover = ({
  onClose,
  onOpenSupport,
}: FeedbackPopoverProps) => {
  const [state, setState] = useState<FeedbackState>({
    message: "",
    error: null,
    isSending: false,
    sent: false,
  })
  const ref = useRef<HTMLDivElement>(null)
  const patch = (partial: Partial<FeedbackState>) =>
    setState((current) => ({ ...current, ...partial }))

  useEffect(() => {
    const closeOnOutsideClick = (event: MouseEvent) => {
      if (!ref.current?.contains(event.target as Node)) onClose()
    }
    document.addEventListener("mousedown", closeOnOutsideClick)
    return () => document.removeEventListener("mousedown", closeOnOutsideClick)
  }, [onClose])

  useEffect(() => {
    if (!state.sent) return
    const timeout = window.setTimeout(onClose, 1500)
    return () => window.clearTimeout(timeout)
  }, [onClose, state.sent])

  const submit = async () => {
    patch({ error: null, isSending: true })
    try {
      await sendFeedback({ message: state.message.trim() })
      patch({ isSending: false, sent: true })
    } catch (error) {
      patch({
        error:
          error instanceof Error ? error.message : "Could not send feedback",
        isSending: false,
      })
    }
  }

  return (
    <div
      className="absolute bottom-full left-0 z-40 mb-2 w-[250px] rounded-[9px] border border-white/10 bg-panel-raised p-3 shadow-2xl shadow-black/40"
      ref={ref}
    >
      {state.sent ? (
        <p className="text-xs text-mint">Sent — thanks!</p>
      ) : (
        <>
          <p className="text-xs font-medium text-zinc-100">Send feedback</p>
          <textarea
            aria-label="Feedback"
            className="mt-2 min-h-[64px] w-full resize-y rounded-md border border-white/10 bg-white/[0.03] px-2.5 py-2 text-xs text-zinc-200 outline-none placeholder:text-zinc-600 focus:border-indigo/45"
            onChange={(event) => patch({ message: event.target.value })}
            placeholder="A bug, an idea, anything — it goes straight to the developer."
            value={state.message}
          />
          {state.error !== null && (
            <p className="mt-1.5 text-[10.5px] leading-4 text-danger">
              {state.error}
            </p>
          )}
          <div className="mt-2.5 flex items-center justify-between gap-2">
            <button
              className="text-left text-[11px] text-ink-muted hover:text-zinc-300"
              onClick={() => {
                onClose()
                onOpenSupport()
              }}
            >
              More support options
            </button>
            <button
              className="rounded-md bg-mint px-3.5 py-1.5 text-[11.5px] font-medium text-emerald-950 disabled:opacity-45"
              disabled={state.isSending || state.message.trim() === ""}
              onClick={() => void submit()}
            >
              {state.isSending ? "Sending…" : "Send"}
            </button>
          </div>
        </>
      )}
    </div>
  )
}
