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

import { Star, X } from "lucide-react"

import { ANKIWEB_REVIEW_URL } from "@/lib/helpChannels"

interface ReviewPromptProps {
  onComplete: () => void
}

export const ReviewPrompt = ({ onComplete }: ReviewPromptProps) => (
  <div className="relative mb-5 flex cursor-pointer items-center gap-3 overflow-hidden rounded-[13px] bg-[linear-gradient(100deg,#b4560a_0%,#e0900f_46%,#f7c14a_100%)] py-3.5 pr-3.5 pl-[17px] transition-transform duration-150 ease-out hover:scale-[1.006]">
    <a
      aria-label="Review Smart Notes on AnkiWeb"
      className="absolute inset-0 z-10 rounded-[13px]"
      href={ANKIWEB_REVIEW_URL}
      onClick={onComplete}
      rel="noreferrer"
      target="_blank"
    />
    <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(500px_150px_at_8%_-45%,rgba(255,244,206,0.34),transparent_72%)]" />
    <Star
      aria-hidden
      className="relative fill-[#ffe49a] text-[#ffe49a]"
      size={23}
    />
    <p className="relative min-w-0 flex-1 text-[14.5px] leading-[1.35] font-extrabold tracking-[-0.01em] text-white">
      Enjoying Smart Notes?
      <span className="ml-2 text-[13px] font-medium text-white/80">
        {" "}
        Leave a review on AnkiWeb to help other Anki users find it.
      </span>
    </p>
    <a
      className="relative z-20 inline-flex shrink-0 items-center rounded-lg bg-[#fff7dc] px-[18px] py-2 text-[12.5px] font-extrabold text-[#7b4807] no-underline transition-transform duration-150 ease-out hover:scale-[1.035]"
      href={ANKIWEB_REVIEW_URL}
      onClick={onComplete}
      rel="noreferrer"
      target="_blank"
    >
      AnkiWeb
    </a>
    <button
      aria-label="Dismiss review invitation"
      className="relative z-20 inline-flex size-6 shrink-0 items-center justify-center rounded-md text-white/60 transition hover:bg-white/10 hover:text-white"
      onClick={onComplete}
      type="button"
    >
      <X aria-hidden className="size-3.5" />
    </button>
  </div>
)
