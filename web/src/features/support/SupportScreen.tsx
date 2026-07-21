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

import { AlertCircle, LifeBuoy, X } from "lucide-react"
import { useState } from "react"

import { sendFeedback } from "@/services/commands"
import { useAppStore } from "@/store/appStore"

const SUPPORT_LINKS = [
  {
    href: "https://ankiweb.net/shared/info/1531888719",
    label: "AnkiWeb · Rate it",
    sub: "Review",
  },
  {
    href: "https://github.com/piazzatron/anki-smart-notes",
    label: "GitHub",
    sub: "Code",
  },
  {
    href: "https://discord.gg/kxGaWpkTGr",
    label: "Discord",
    sub: "Chat",
  },
  {
    href: "https://docs.smart-notes.xyz",
    label: "Docs",
    sub: "Guides",
  },
]

interface FeedbackFormState {
  message: string
  error: string | null
  isSending: boolean
  sent: boolean
}

export const SupportScreen = () => {
  const state = useAppStore((store) => store.state)
  const [form, setForm] = useState<FeedbackFormState>({
    message: "",
    error: null,
    isSending: false,
    sent: false,
  })
  const patch = (partial: Partial<FeedbackFormState>) =>
    setForm((current) => ({ ...current, ...partial }))

  if (state === null) return <SupportSkeleton />

  const submit = async () => {
    patch({ error: null, isSending: true, sent: false })
    try {
      await sendFeedback({ message: form.message.trim() })
      patch({ message: "", isSending: false, sent: true })
    } catch (error) {
      patch({
        error:
          error instanceof Error ? error.message : "Could not send feedback",
        isSending: false,
      })
    }
  }

  return (
    <section
      className="flex min-h-0 flex-1 flex-col"
      data-testid="support-screen"
    >
      <header className="shrink-0 border-b border-white/[0.065] px-6 py-5">
        <div className="flex items-center gap-2">
          <LifeBuoy aria-hidden className="size-5 text-indigo-soft" />
          <h1 className="text-[21px] leading-tight font-bold tracking-[-0.025em] text-zinc-100">
            Support &amp; Bugs
          </h1>
        </div>
        <p className="mt-1.5 text-xs text-ink-muted">
          Get help, read the docs, or send us a bug or feature request.
        </p>
      </header>

      <div className="min-h-0 flex-1 overflow-y-auto px-6 py-5">
        <div className="overflow-hidden rounded-xl border border-white/[0.08] bg-white/[0.02]">
          <h2 className="border-b border-white/[0.06] px-4 py-3 text-[13px] font-semibold text-zinc-100">
            Send us a message
          </h2>
          <div className="p-4">
            {form.error !== null && (
              <div className="mb-3 flex items-start gap-2 rounded-lg border border-red-300/15 bg-red-300/[0.06] px-3 py-2 text-xs text-danger">
                <AlertCircle aria-hidden className="mt-0.5 size-3.5 shrink-0" />
                <p className="min-w-0 flex-1">{form.error}</p>
                <button
                  aria-label="Dismiss error"
                  onClick={() => patch({ error: null })}
                >
                  <X aria-hidden className="size-3.5" />
                </button>
              </div>
            )}
            <textarea
              className="min-h-[116px] w-full resize-y rounded-md border border-white/10 bg-white/[0.03] px-3 py-2.5 text-xs leading-[1.5] text-zinc-200 outline-none placeholder:text-zinc-600 focus:border-indigo/45"
              onChange={(event) =>
                patch({ message: event.target.value, sent: false })
              }
              placeholder="What's up? Bugs, ideas, questions — it goes straight to the developer."
              value={form.message}
            />
            <div className="mt-3 flex items-center justify-between">
              <p
                className={`text-[11px] ${form.sent ? "text-mint" : "text-ink-faint"}`}
              >
                {form.sent
                  ? "Sent — thanks!"
                  : "Goes straight to the developer."}
              </p>
              <button
                className="rounded-md border border-white/10 bg-white/[0.07] px-4 py-2 text-xs font-semibold text-zinc-200 hover:bg-white/10 disabled:opacity-45"
                disabled={form.isSending || form.message.trim() === ""}
                onClick={() => void submit()}
              >
                {form.isSending ? "Sending…" : "Send"}
              </button>
            </div>
          </div>
        </div>

        <div className="mt-2.5 grid grid-cols-4 gap-2">
          {SUPPORT_LINKS.map((link) => (
            <a
              className="flex min-w-0 flex-col rounded-lg border border-white/[0.08] bg-white/[0.02] px-3 py-2.5 transition hover:border-white/15 hover:bg-white/[0.04]"
              href={link.href}
              key={link.label}
              rel="noreferrer"
              target="_blank"
            >
              <span className="truncate text-[12.5px] font-semibold text-zinc-200">
                {link.label}
              </span>
              <span className="mt-0.5 text-[10.5px] text-ink-muted">
                {link.sub}
              </span>
            </a>
          ))}
        </div>

        <div className="mt-4 px-0.5">
          <p className="text-xs leading-5 text-zinc-400">
            Made by Michael — a one-person project from the Anki community.
          </p>
          <p className="mt-1.5 text-[11px] text-ink-faint">
            Smart Notes v{state.appVersion} ·{" "}
            <a
              className="hover:text-zinc-400"
              href="https://docs.smart-notes.xyz"
              rel="noreferrer"
              target="_blank"
            >
              Changelog
            </a>
          </p>
        </div>
      </div>
    </section>
  )
}

const SupportSkeleton = () => (
  <section
    aria-label="Loading Support"
    className="flex min-h-0 flex-1 animate-pulse flex-col"
  >
    <div className="h-[86px] border-b border-white/[0.065] px-6 py-5">
      <div className="h-5 w-44 rounded bg-white/[0.06]" />
      <div className="mt-3 h-3 w-80 rounded bg-white/[0.035]" />
    </div>
    <div className="p-6">
      <div className="h-64 rounded-xl bg-white/[0.025]" />
    </div>
  </section>
)
