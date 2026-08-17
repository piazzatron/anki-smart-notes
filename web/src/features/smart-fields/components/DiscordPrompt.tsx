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

import { X } from "lucide-react"

import { DiscordMark } from "@/components/shared/DiscordMark"
import { DISCORD_URL } from "@/lib/helpChannels"

interface DiscordPromptProps {
  onDismiss: () => void
}

export const DiscordPrompt = ({ onDismiss }: DiscordPromptProps) => (
  <div className="relative mb-5 flex cursor-pointer items-center gap-3 overflow-hidden rounded-[13px] bg-[linear-gradient(100deg,#3C45A5_0%,#5865F2_42%,#9B4DFF_100%)] py-3.5 pr-3.5 pl-[17px] transition-transform duration-150 ease-out hover:scale-[1.006]">
    <a
      aria-label="Join the Smart Notes Discord"
      className="absolute inset-0 z-10 rounded-[13px]"
      href={DISCORD_URL}
      rel="noreferrer"
      target="_blank"
    />
    <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(460px_140px_at_10%_-40%,rgba(180,200,255,0.3),transparent_72%)]" />
    <DiscordMark className="relative text-white" size={23} />
    <p className="relative min-w-0 flex-1 text-[14.5px] leading-[1.35] font-extrabold tracking-[-0.01em] text-white">
      Come say hi in the Discord
      <span className="text-[13px] font-medium text-white/80">
        {" "}
        — swap prompts and request features.
      </span>
    </p>
    <a
      className="relative z-20 inline-flex shrink-0 items-center rounded-lg bg-white px-[18px] py-2 text-[12.5px] font-extrabold text-[#6B3FD4] no-underline transition-transform duration-150 ease-out hover:scale-[1.035]"
      href={DISCORD_URL}
      rel="noreferrer"
      target="_blank"
    >
      Join
    </a>
    <button
      aria-label="Dismiss Discord invitation"
      className="relative z-20 inline-flex size-6 shrink-0 items-center justify-center rounded-md text-white/60 transition hover:bg-white/10 hover:text-white"
      onClick={onDismiss}
      type="button"
    >
      <X aria-hidden className="size-3.5" />
    </button>
  </div>
)
