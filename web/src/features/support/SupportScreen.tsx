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

import { AnkiMark, GithubMark } from "@/components/shared/BrandMarks"
import { DiscordMark } from "@/components/shared/DiscordMark"
import { FeedbackDialog } from "@/components/shared/FeedbackDialog"
import { PageTitle } from "@/components/shared/PageTitle"
import { ScreenSkeleton } from "@/components/shared/ScreenSkeleton"
import { DISCORD_URL, SUPPORT_EMAIL } from "@/lib/helpChannels"
import { useAppStore } from "@/store/appStore"

const REFERENCE_LINKS = [
  {
    href: `mailto:${SUPPORT_EMAIL}`,
    label: "Email us",
    mark: <span className="text-[19px]">✉️</span>,
    sub: SUPPORT_EMAIL,
  },
  {
    href: "https://ankiweb.net/shared/info/1531888719",
    label: "AnkiWeb",
    mark: <AnkiMark />,
    sub: "Leave a review / see docs.",
  },
  {
    href: "https://github.com/piazzatron/anki-smart-notes",
    label: "GitHub",
    mark: <GithubMark />,
    sub: undefined,
  },
]

export const SupportScreen = () => {
  const state = useAppStore((store) => store.state)

  if (state === null)
    return (
      <ScreenSkeleton ariaLabel="Loading Support" contentClassName="h-64" />
    )

  return (
    <section
      className="flex min-h-0 flex-1 flex-col"
      data-testid="support-screen"
    >
      <header className="shrink-0 border-b border-white/[0.05] px-6 pt-5 pb-3.5">
        <PageTitle>Support</PageTitle>
      </header>

      <div className="min-h-0 flex-1 overflow-y-auto px-6 py-5">
        <div className="relative flex items-center gap-[15px] overflow-hidden rounded-[13px] bg-[linear-gradient(100deg,#3C45A5_0%,#5865F2_42%,#9B4DFF_100%)] py-[17px] pr-4 pl-[19px]">
          <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(460px_140px_at_10%_-40%,rgba(180,200,255,0.3),transparent_72%)]" />
          <DiscordMark className="relative text-white" size={31} />
          <div className="relative min-w-0 flex-1">
            <h2 className="text-base font-extrabold tracking-[-0.01em] text-white">
              Join the Discord
            </h2>
            <p className="mt-[3px] text-[12.5px] text-white/80">
              The fastest way to get help, request a feature, or report a bug.
            </p>
          </div>
          <a
            className="relative shrink-0 rounded-lg bg-white px-[22px] py-2.5 text-[13px] font-extrabold text-[#6B3FD4]"
            href={DISCORD_URL}
            rel="noreferrer"
            target="_blank"
          >
            Join
          </a>
        </div>

        <div className="mt-[9px] flex items-center gap-[15px] rounded-[13px] bg-white/[0.07] py-4 pr-4 pl-[19px]">
          <span aria-hidden className="shrink-0 text-2xl leading-none">
            🐛
          </span>
          <div className="min-w-0 flex-1">
            <h2 className="text-base font-extrabold tracking-[-0.01em] text-zinc-100">
              Submit a bug / request a feature
            </h2>
            <p className="mt-[3px] text-[12.5px] text-zinc-400">
              Something broken or wrong? Message the poor developer directly.
            </p>
          </div>
          <FeedbackDialog>
            <button
              className="shrink-0 rounded-[9px] bg-[#5b6fe8] px-5 py-2.5 text-[13px] font-extrabold text-white"
              type="button"
            >
              Send it
            </button>
          </FeedbackDialog>
        </div>

        <div className="mt-[9px] grid grid-cols-3 gap-[9px]">
          {REFERENCE_LINKS.map((link) => (
            <a
              className="flex min-w-0 items-center gap-3 rounded-[13px] bg-white/[0.05] px-4 py-3.5"
              href={link.href}
              key={link.label}
              rel="noreferrer"
              target="_blank"
            >
              <span className="flex shrink-0" aria-hidden>
                {link.mark}
              </span>
              <span className="min-w-0">
                <span className="block text-sm font-bold text-zinc-100">
                  {link.label}
                </span>
                <span className="mt-0.5 block truncate text-[11.5px] text-zinc-400">
                  {link.sub}
                </span>
              </span>
            </a>
          ))}
        </div>

        <footer className="mt-[18px] px-0.5">
          <p className="text-xs leading-[1.55] text-zinc-400">
            <a
              className="text-zinc-400 hover:text-zinc-200"
              href="https://smart-notes.xyz"
              rel="noreferrer"
              target="_blank"
            >
              Smart Notes
            </a>{" "}
            by Michael Piazza / Rosebud Labs, LLC.
          </p>
          <p className="mt-2.5 text-[11px] text-zinc-600">
            © 2026 · v{state.appVersion} ·{" "}
            <a
              className="text-zinc-400 hover:text-zinc-200"
              href="https://docs.smart-notes.xyz"
              rel="noreferrer"
              target="_blank"
            >
              Changelog
            </a>
          </p>
        </footer>
      </div>
    </section>
  )
}
