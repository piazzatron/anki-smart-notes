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

import { ConnectionNotice } from "@/components/shared/ConnectionNotice"
import { openSiteLink, SITE_LINKS } from "@/lib/siteLinks"
import type { Connection } from "@/store/appStore"

interface WelcomeScreenProps {
  connection: Connection
}

export const WelcomeScreen = ({ connection }: WelcomeScreenProps) => (
  <main className="flex h-full min-h-0 flex-col bg-canvas text-ink">
    <ConnectionNotice connection={connection} />
    <div className="flex min-h-0 flex-1 items-center justify-center px-6 py-10 text-center">
      <div className="w-full max-w-sm">
        <p className="text-[32px] font-extrabold tracking-[-0.04em] text-zinc-100">
          Smart Notes ✨
        </p>
        <h1 className="mt-6 text-xl font-bold text-zinc-100">
          Welcome to Smart Notes
        </h1>
        <p className="mt-2 text-sm leading-6 text-ink-muted">
          Create an account to start adding generated text, voice, and images to
          your Anki cards.
        </p>
        <button
          className="mt-7 w-full rounded-xl bg-mint px-5 py-3 text-sm font-extrabold text-emerald-950 transition hover:bg-emerald-300"
          onClick={() => openSiteLink(SITE_LINKS.startTrial)}
          type="button"
        >
          Start Free Trial
        </button>
        <button
          className="mt-4 text-xs font-semibold text-indigo-soft transition hover:text-white"
          onClick={() => openSiteLink(SITE_LINKS.signIn)}
          type="button"
        >
          Already have an account? Sign in
        </button>
      </div>
    </div>
  </main>
)
